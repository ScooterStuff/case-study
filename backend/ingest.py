"""JSON datasets -> Postgres (+ pgvector embeddings).

Modes:
  python backend/ingest.py --rebuild       # tables + embeddings via API (needs key,
                                           # or MOCK_EMBEDDINGS=1)
  python backend/ingest.py --load-seed     # restore committed seed.sql.gz (no keys)
  python backend/ingest.py --dump-seed     # regenerate backend/data/seed.sql.gz

Default: --load-seed if backend/data/seed.sql.gz exists, else --rebuild.
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app import config  # noqa: E402
from backend.app.embeddings import embed_batch  # noqa: E402

logger = logging.getLogger("ingest")
DATA = Path(__file__).parent / "data"

SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS embeddings, repair_causes, repair_guides, compatibility,
  part_replaces, part_symptoms, parts CASCADE;

CREATE TABLE parts (
  ps_number      TEXT PRIMARY KEY,
  mpn            TEXT NOT NULL,
  brand          TEXT NOT NULL,
  title          TEXT NOT NULL,
  appliance_type TEXT NOT NULL CHECK (appliance_type IN ('refrigerator','dishwasher')),
  price          NUMERIC(10,2),
  currency       TEXT DEFAULT 'USD',
  availability   TEXT,
  description    TEXT,
  install_difficulty TEXT,
  install_time   TEXT,
  avg_repair_rating REAL,
  repair_rating_count INTEGER,
  rating         REAL,
  review_count   INTEGER,
  image_url      TEXT,
  product_url    TEXT NOT NULL,
  video_url      TEXT,
  search_tsv     tsvector GENERATED ALWAYS AS (
                   to_tsvector('english', coalesce(title,'') || ' ' ||
                   coalesce(mpn,'') || ' ' || coalesce(description,''))) STORED
);
CREATE INDEX idx_parts_tsv ON parts USING GIN (search_tsv);

CREATE TABLE part_symptoms (
  ps_number TEXT REFERENCES parts(ps_number),
  symptom   TEXT NOT NULL
);
CREATE INDEX idx_symptom ON part_symptoms(symptom);

CREATE TABLE part_replaces (
  ps_number TEXT REFERENCES parts(ps_number),
  old_mpn   TEXT NOT NULL
);
CREATE INDEX idx_old_mpn ON part_replaces(old_mpn);

CREATE TABLE compatibility (
  ps_number    TEXT REFERENCES parts(ps_number),
  brand        TEXT,
  model_number TEXT NOT NULL,
  model_desc   TEXT,
  source       TEXT DEFAULT 'cross_ref',
  PRIMARY KEY (ps_number, model_number)
);
CREATE INDEX idx_model ON compatibility(model_number);

CREATE TABLE repair_guides (
  id        SERIAL PRIMARY KEY,
  appliance TEXT NOT NULL,
  symptom   TEXT NOT NULL,
  url       TEXT
);

CREATE TABLE repair_causes (
  guide_id  INTEGER REFERENCES repair_guides(id),
  rank      INTEGER,
  cause     TEXT NOT NULL,
  body      TEXT NOT NULL,
  part_types TEXT
);

CREATE TABLE embeddings (
  id         SERIAL PRIMARY KEY,
  collection TEXT NOT NULL CHECK (collection IN ('repair_chunks','part_docs','support_snippets')),
  document   TEXT NOT NULL,
  metadata   JSONB NOT NULL,
  embedding  vector(%(dims)s)
);
CREATE INDEX idx_emb_collection ON embeddings(collection);
CREATE INDEX idx_emb_hnsw ON embeddings USING hnsw (embedding vector_cosine_ops);
"""


def load_json(name: str) -> list[dict]:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def rebuild(conn: psycopg.Connection) -> None:
    parts = load_json("parts.json")
    compat = load_json("compatibility.json")
    guides = load_json("repair_guides.json")

    conn.execute(SCHEMA % {"dims": config.settings.embedding_dims})
    register_vector(conn)  # NOTE: must precede cursor creation (cursors snapshot adapters)

    with conn.cursor() as cur:
        for p in parts:
            stories = p.get("repair_stories", [])
            difficulties = Counter(s["difficulty"] for s in stories if s.get("difficulty"))
            cur.execute(
                """INSERT INTO parts (ps_number, mpn, brand, title, appliance_type,
                     price, availability, description, install_difficulty, install_time,
                     rating, review_count, image_url, product_url, video_url)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    p["ps_number"],
                    p["mpn"],
                    p["brand"],
                    p["title"],
                    p["appliance_type"],
                    p.get("price"),
                    p.get("availability"),
                    p.get("description"),
                    p.get("install_difficulty")
                    or (difficulties.most_common(1)[0][0] if difficulties else None),
                    p.get("install_time"),
                    p.get("rating"),
                    p.get("review_count"),
                    (p.get("images") or [None])[0],
                    p["source_url"],
                    (p.get("videos") or [{}])[0].get("url"),
                ),
            )
            cur.executemany(
                "INSERT INTO part_symptoms VALUES (%s,%s)",
                [(p["ps_number"], s) for s in p.get("symptoms", [])],
            )
            cur.executemany(
                "INSERT INTO part_replaces VALUES (%s,%s)",
                [(p["ps_number"], m) for m in p.get("replaces", [])],
            )

        known = {p["ps_number"] for p in parts}
        skipped = 0
        for row in compat:
            if row["ps_number"] not in known:
                skipped += 1  # NOTE: FK to parts; model-page rows for unstocked parts are dropped
                continue
            cur.execute(
                """INSERT INTO compatibility VALUES (%s,%s,%s,%s,%s)
                   ON CONFLICT DO NOTHING""",
                (
                    row["ps_number"],
                    row.get("brand"),
                    row["model_number"],
                    row.get("description"),
                    row.get("source", "cross_ref"),
                ),
            )

        docs: list[tuple[str, str, dict]] = []  # (collection, document, metadata)
        for g in guides:
            cur.execute(
                "INSERT INTO repair_guides (appliance, symptom, url) VALUES (%s,%s,%s) RETURNING id",
                (g["appliance"], g["symptom"], g.get("source_url")),
            )
            gid = cur.fetchone()[0]
            for c in g.get("causes", []):
                cur.execute(
                    "INSERT INTO repair_causes VALUES (%s,%s,%s,%s,%s)",
                    (gid, c["rank"], c["name"], c["text"], ", ".join(c.get("part_links", []))),
                )
                body = c["text"]
                chunks = [body] if len(body) <= 1200 else _split(body)
                for chunk in chunks:
                    docs.append(
                        (
                            "repair_chunks",
                            f"{g['appliance']} — {g['symptom']} — cause {c['rank']}: {c['name']}\n{chunk}",
                            {
                                "appliance": g["appliance"],
                                "symptom": g["symptom"],
                                "rank": c["rank"],
                                "guide_id": gid,
                                "cause": c["name"],
                            },
                        )
                    )
            if not g.get("causes"):
                docs.append(
                    (
                        "repair_chunks",
                        f"{g['appliance']} — {g['symptom']} (summary)\n{g.get('intro', '')}",
                        {
                            "appliance": g["appliance"],
                            "symptom": g["symptom"],
                            "rank": 0,
                            "guide_id": gid,
                            "cause": "summary",
                        },
                    )
                )

        for p in parts:
            doc = (
                f"{p['title']} ({p['ps_number']} / {p['mpn']}) by {p['brand']}. "
                f"Fixes: {', '.join(p.get('symptoms', []))}. {(p.get('description') or '')[:1500]}"
            )
            docs.append(
                (
                    "part_docs",
                    doc,
                    {"ps_number": p["ps_number"], "appliance_type": p["appliance_type"], "brand": p["brand"]},
                )
            )
            for q in p.get("qna", []):
                if q.get("question"):
                    docs.append(
                        (
                            "support_snippets",
                            f"Q: {q['question']}\nA: {q.get('answer', '')}",
                            {"ps_number": p["ps_number"], "kind": "qna"},
                        )
                    )
            for s in p.get("repair_stories", [])[:5]:
                if s.get("text"):
                    docs.append(
                        ("support_snippets", s["text"][:1500], {"ps_number": p["ps_number"], "kind": "story"})
                    )

        texts = [d[1] for d in docs]
        n_tokens = sum(len(t) for t in texts) / 4
        logger.info(
            "embedding %d docs (~%dk tokens, est cost $%.4f)%s",
            len(docs),
            n_tokens / 1000,
            n_tokens / 1e6 * 0.02,
            " [MOCK]" if config.settings.mock_embeddings else "",
        )
        vectors = embed_batch(texts)
        import numpy as np

        for (collection, document, metadata), vec in zip(docs, vectors, strict=True):
            cur.execute(
                "INSERT INTO embeddings (collection, document, metadata, embedding) VALUES (%s,%s,%s,%s)",
                (collection, document, json.dumps(metadata), np.array(vec)),
            )

    conn.commit()
    for table in (
        "parts",
        "part_symptoms",
        "part_replaces",
        "compatibility",
        "repair_guides",
        "repair_causes",
        "embeddings",
    ):
        n = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]  # noqa: S608
        logger.info("%-15s %d rows", table, n)
    if skipped:
        logger.info("(skipped %d compatibility rows for parts outside the dataset)", skipped)


def _split(body: str, limit: int = 1200, overlap: int = 100) -> list[str]:
    paras = body.split("\n\n") if "\n\n" in body else [body]
    chunks, cur = [], ""
    for para in paras:
        if len(cur) + len(para) > limit and cur:
            chunks.append(cur)
            cur = cur[-overlap:] + " " + para
        else:
            cur = (cur + "\n\n" + para).strip()
    while len(cur) > limit:
        chunks.append(cur[:limit])
        cur = cur[limit - overlap :]
    if cur:
        chunks.append(cur)
    return chunks


def load_seed(conn: psycopg.Connection, seed: Path) -> None:
    sql = gzip.decompress(seed.read_bytes()).decode()
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    conn.execute(sql)
    conn.execute("SET search_path TO public")  # the dump blanks search_path for its session
    conn.commit()
    n = conn.execute("SELECT count(*) FROM parts").fetchone()[0]
    logger.info("seed restored: %d parts", n)


def dump_seed(seed: Path) -> None:
    pg_dump = shutil.which("pg_dump")
    if not pg_dump:
        try:
            import pgserver

            pg_dump = str(Path(pgserver.__file__).parent / "pginstall" / "bin" / "pg_dump")
        except ImportError:
            pass
    if not pg_dump or not Path(pg_dump).exists():
        raise SystemExit("pg_dump not found - run inside an environment with postgres client tools")
    out = subprocess.run(  # noqa: S603
        [pg_dump, "--no-owner", "--clean", "--if-exists", config.settings.database_url],
        capture_output=True,
        check=True,
    )
    seed.write_bytes(gzip.compress(out.stdout, 6))
    logger.info("wrote %s (%d KB)", seed, seed.stat().st_size // 1024)


def main() -> None:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--rebuild", action="store_true")
    mode.add_argument("--load-seed", action="store_true")
    mode.add_argument("--dump-seed", action="store_true")
    args = ap.parse_args()

    seed = DATA / "seed.sql.gz"
    if args.dump_seed:
        dump_seed(seed)
        return
    with psycopg.connect(config.settings.database_url, autocommit=False) as conn:
        if args.load_seed or (not args.rebuild and seed.exists()):
            load_seed(conn, seed)
        else:
            rebuild(conn)


if __name__ == "__main__":
    main()
