"""Deterministic SQL + pgvector retrieval. No LLM anywhere in this module.

The split is deliberate (TRADEOFFS.md D1/D2): anything that would be dangerous
to hallucinate (prices, stock, compatibility) is answered by plain SQL;
fuzzy natural language (symptoms, descriptions) is answered by vectors.
Compatibility is a database join, NEVER an LLM guess.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import psycopg
from pgvector.psycopg import register_vector

from backend.app import config
from backend.app.embeddings import embed_one

_conn: psycopg.Connection | None = None


def get_conn() -> psycopg.Connection:
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg.connect(config.settings.database_url, autocommit=True)
        register_vector(_conn)
    return _conn


def norm_number(value: str) -> str:
    return re.sub(r"\s+", "", value).strip().upper().strip("#")


PART_COLS = (
    "ps_number, mpn, brand, title, appliance_type, price, availability, "
    "description, install_difficulty, install_time, rating, review_count, "
    "image_url, product_url, video_url"
)


def _part_row(row: tuple) -> dict[str, Any]:
    keys = [c.strip() for c in PART_COLS.split(",")]
    d = dict(zip(keys, row, strict=True))
    if d.get("price") is not None:
        d["price"] = float(d["price"])
    return d


# ------------------------------------------------------------------ exact facts


def get_part(ps_or_mpn: str) -> dict | None:
    """Exact lookup by PS number, MPN, or superseded (replaced) MPN."""
    key = norm_number(ps_or_mpn)
    conn = get_conn()
    row = conn.execute(
        f"SELECT {PART_COLS} FROM parts WHERE ps_number = %s OR upper(mpn) = %s", (key, key)
    ).fetchone()
    if row is None:
        qualified = ", ".join("p." + c.strip() for c in PART_COLS.split(","))
        row = conn.execute(
            f"""SELECT {qualified} FROM parts p
                JOIN part_replaces r ON r.ps_number = p.ps_number
                WHERE upper(r.old_mpn) = %s LIMIT 1""",
            (key,),
        ).fetchone()
        if row is None:
            return None
        part = _part_row(row)
        part["matched_via"] = f"replaces {key}"
        return part
    part = _part_row(row)
    part["symptoms"] = [
        r[0]
        for r in conn.execute("SELECT symptom FROM part_symptoms WHERE ps_number = %s", (part["ps_number"],))
    ]
    part["replaces"] = [
        r[0]
        for r in conn.execute("SELECT old_mpn FROM part_replaces WHERE ps_number = %s", (part["ps_number"],))
    ]
    return part


@dataclass
class CompatResult:
    status: str  # verified_fit | no_match_found | unknown_model | unknown_part
    ps_number: str
    model_number: str
    evidence: dict = field(default_factory=dict)


def check_compat(ps_number: str, model: str) -> CompatResult:
    """Deterministic compatibility verdict from the scraped cross-reference data.

    Honesty matters: the scraped cross-reference is partial (paginated source),
    so 'no_match_found' means "not in our verified list", NOT "incompatible".
    """
    ps, model = norm_number(ps_number), norm_number(model)
    conn = get_conn()
    part = get_part(ps)
    if part is None:
        return CompatResult("unknown_part", ps, model)
    ps = part["ps_number"]

    hit = conn.execute(
        "SELECT source, model_desc FROM compatibility WHERE ps_number = %s AND model_number = %s", (ps, model)
    ).fetchone()
    total = conn.execute("SELECT count(*) FROM compatibility WHERE ps_number = %s", (ps,)).fetchone()[0]
    model_known = conn.execute(
        "SELECT count(*) FROM compatibility WHERE model_number = %s", (model,)
    ).fetchone()[0]

    evidence = {
        "verified_model_count_for_part": total,
        "model_seen_in_data": bool(model_known),
        "part_title": part["title"],
        "part_appliance": part["appliance_type"],
    }
    if hit:
        evidence.update(source=hit[0], model_desc=hit[1])
        return CompatResult("verified_fit", ps, model, evidence)
    if model_known:
        evidence["parts_verified_for_model"] = model_known
        return CompatResult("no_match_found", ps, model, evidence)
    return CompatResult("unknown_model", ps, model, evidence)


def parts_for_model(model: str, symptom: str | None = None, limit: int = 10) -> list[dict]:
    model = norm_number(model)
    conn = get_conn()
    sql = f"""SELECT DISTINCT {", ".join("p." + c.strip() for c in PART_COLS.split(","))}
              FROM parts p JOIN compatibility c ON c.ps_number = p.ps_number
              WHERE c.model_number = %s"""
    params: list = [model]
    if symptom:
        sql += """ AND p.ps_number IN (
                     SELECT ps_number FROM part_symptoms WHERE symptom ILIKE %s)"""
        params.append(f"%{symptom}%")
    sql += " ORDER BY p.review_count DESC NULLS LAST LIMIT %s"
    params.append(limit)
    return [_part_row(r) for r in conn.execute(sql, params)]


# --------------------------------------------------------------------- search


def keyword_search(q: str, appliance: str | None = None, limit: int = 8) -> list[dict]:
    conn = get_conn()
    sql = f"""SELECT {PART_COLS}, ts_rank(search_tsv, websearch_to_tsquery('english', %s)) AS rank
              FROM parts WHERE search_tsv @@ websearch_to_tsquery('english', %s)"""
    params: list = [q, q]
    if appliance:
        sql += " AND appliance_type = %s"
        params.append(appliance)
    sql += " ORDER BY rank DESC LIMIT %s"
    params.append(limit)
    return [_part_row(r[:-1]) for r in conn.execute(sql, params)]


def vector_search_parts(q: str, appliance: str | None = None, k: int = 8) -> list[dict]:
    conn = get_conn()
    vec = np.array(embed_one(q))
    sql = """SELECT metadata->>'ps_number' FROM embeddings
             WHERE collection = 'part_docs'"""
    params: list = []
    if appliance:
        sql += " AND metadata->>'appliance_type' = %s"
        params.append(appliance)
    sql += " ORDER BY embedding <=> %s LIMIT %s"
    params += [vec, k]
    ps_numbers = [r[0] for r in conn.execute(sql, params)]
    parts = [get_part(ps) for ps in ps_numbers]
    return [p for p in parts if p]


def hybrid_search(q: str, appliance: str | None = None, k: int = 8) -> list[dict]:
    """Reciprocal-rank-fusion of tsvector keyword search and vector search."""
    keyword = keyword_search(q, appliance, limit=k)
    vector = vector_search_parts(q, appliance, k=k)
    scores: dict[str, float] = {}
    parts: dict[str, dict] = {}
    for results, weight in ((keyword, 1.0), (vector, 1.0)):
        for rank, part in enumerate(results):
            ps = part["ps_number"]
            scores[ps] = scores.get(ps, 0.0) + weight / (60 + rank)
            parts.setdefault(ps, part)
    ranked = sorted(scores, key=scores.get, reverse=True)[:k]
    return [parts[ps] for ps in ranked]


def search_repairs(symptom_text: str, appliance: str, k: int = 6) -> list[dict]:
    """Semantic search over repair-guide cause chunks; rank preserved in metadata."""
    conn = get_conn()
    vec = np.array(embed_one(symptom_text))
    rows = conn.execute(
        """SELECT document, metadata, 1 - (embedding <=> %s) AS similarity
           FROM embeddings
           WHERE collection = 'repair_chunks' AND metadata->>'appliance' = %s
           ORDER BY embedding <=> %s LIMIT %s""",
        (vec, appliance, vec, k),
    ).fetchall()
    out = []
    for doc, meta, sim in rows:
        meta = meta if isinstance(meta, dict) else json.loads(meta)
        out.append({"document": doc, "similarity": float(sim), **meta})
    return out


def guide_causes(guide_id: int) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        """SELECT g.symptom, g.appliance, g.url, c.rank, c.cause, c.body
           FROM repair_guides g LEFT JOIN repair_causes c ON c.guide_id = g.id
           WHERE g.id = %s ORDER BY c.rank""",
        (guide_id,),
    ).fetchall()
    return [
        {"symptom": r[0], "appliance": r[1], "url": r[2], "rank": r[3], "cause": r[4], "body": r[5]}
        for r in rows
        if r[3] is not None
    ]


def search_support(q: str, ps_number: str | None = None, k: int = 4) -> list[dict]:
    conn = get_conn()
    vec = np.array(embed_one(q))
    sql = "SELECT document, metadata FROM embeddings WHERE collection = 'support_snippets'"
    params: list = []
    if ps_number:
        sql += " AND metadata->>'ps_number' = %s"
        params.append(norm_number(ps_number))
    sql += " ORDER BY embedding <=> %s LIMIT %s"
    params += [vec, k]
    out = []
    for doc, meta in conn.execute(sql, params):
        meta = meta if isinstance(meta, dict) else json.loads(meta)
        out.append({"document": doc, **meta})
    return out
