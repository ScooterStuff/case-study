"""The agent's six tools. Each returns {"data": ..., "ui_block": ...} where
ui_block is an optional pre-shaped payload the frontend renders as a rich
component. Tool *facts* come exclusively from the Phase 2 retrieval layer.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

from backend.app import retrieval

PS_RE = re.compile(r"PS\d{5,9}")


# ------------------------------------------------------------------ schemas


class SearchPartsIn(BaseModel):
    query: str = Field(description="What the customer is looking for, in their words")
    appliance_type: Literal["refrigerator", "dishwasher"] | None = Field(
        None, description="Filter when the appliance is known"
    )


class PartDetailsIn(BaseModel):
    part_identifier: str = Field(
        description="PS number, manufacturer part number, or an old superseded number"
    )


class CompatibilityIn(BaseModel):
    part_identifier: str
    model_number: str = Field(description="The appliance model number, e.g. WDT780SAEM1")


class DiagnoseIn(BaseModel):
    symptom_description: str
    appliance_type: Literal["refrigerator", "dishwasher"]
    brand: str | None = None


class InstallGuideIn(BaseModel):
    part_identifier: str


# ------------------------------------------------------------------- helpers


def _card(p: dict) -> dict:
    return {
        k: p.get(k)
        for k in (
            "ps_number",
            "mpn",
            "brand",
            "title",
            "price",
            "availability",
            "install_difficulty",
            "install_time",
            "rating",
            "review_count",
            "image_url",
            "product_url",
            "appliance_type",
        )
    }


# --------------------------------------------------------------------- tools


def search_parts(query: str, appliance_type: str | None = None) -> dict:
    parts = retrieval.hybrid_search(query, appliance_type, k=6)
    return {
        "data": {"results": [_card(p) for p in parts], "query": query},
        "ui_block": {"type": "product_list", "products": [_card(p) for p in parts]} if parts else None,
    }


def get_part_details(part_identifier: str) -> dict:
    part = retrieval.get_part(part_identifier)
    if part is None:
        return {
            "data": {
                "found": False,
                "identifier": part_identifier,
                "note": "No part with that number in our catalog. Ask the user to double-check it.",
            },
            "ui_block": None,
        }
    return {
        "data": {"found": True, **part},
        "ui_block": {
            "type": "product_card",
            "product": _card(part),
            "description": (part.get("description") or "")[:400],
            "symptoms": part.get("symptoms", []),
        },
    }


def check_compatibility(part_identifier: str, model_number: str) -> dict:
    res = retrieval.check_compat(part_identifier, model_number)
    sample = []
    if res.status == "no_match_found":
        sample = [p["title"] for p in retrieval.parts_for_model(model_number, limit=5)]
    honesty = {
        "verified_fit": "Verified against PartSelect's cross-reference data.",
        "no_match_found": "Not in our verified list - the scraped cross-reference is partial, "
        "so phrase as 'not in our verified compatibility list', never a hard 'incompatible'.",
        "unknown_model": "We have no data for this model number - it may be mistyped.",
        "unknown_part": "No part with that number in our catalog.",
    }[res.status]
    return {
        "data": {
            "status": res.status,
            "ps_number": res.ps_number,
            "model_number": res.model_number,
            "evidence": res.evidence,
            "honesty_note": honesty,
            "parts_verified_for_model_sample": sample,
        },
        "ui_block": {
            "type": "compat_result",
            "verdict": res.status,
            "part": res.ps_number,
            "model": res.model_number,
            "evidence_count": res.evidence.get("verified_model_count_for_part", 0),
            "honesty_note": honesty,
        },
    }


def diagnose_issue(symptom_description: str, appliance_type: str, brand: str | None = None) -> dict:
    chunks = retrieval.search_repairs(symptom_description, appliance_type, k=6)
    causes: list[dict] = []
    if chunks:
        # Best-matching FULL guide wins (rank>0 = it has ranked causes); summary
        # guides only if nothing better. Then present ALL of the winning guide's
        # causes in PartSelect's likelihood order, not just the retrieved chunks.
        top_guide = next((c["guide_id"] for c in chunks if c.get("rank")), None)
        full = retrieval.guide_causes(top_guide) if top_guide is not None else []
        causes = [
            {
                "symptom": c["symptom"],
                "rank": c["rank"],
                "cause": c["cause"],
                "detail": (c["body"] or "")[:600],
            }
            for c in full
        ][:6]
        if not causes:  # only summary-level guides matched
            causes = [
                {"symptom": c["symptom"], "rank": i + 1, "cause": c["symptom"], "detail": c["document"][:600]}
                for i, c in enumerate(chunks[:4])
            ]
    q = f"{brand or ''} {appliance_type} {symptom_description}"
    parts = retrieval.hybrid_search(q, appliance_type, k=5)
    if brand:
        branded = [p for p in parts if brand.lower() in p["brand"].lower()]
        parts = branded or parts
    return {
        "data": {"causes": causes, "suggested_parts": [_card(p) for p in parts]},
        "ui_block": {
            "type": "diagnosis",
            "causes": [{"rank": c["rank"], "cause": c["cause"]} for c in causes],
            "suggested_parts": [_card(p) for p in parts[:4]],
        },
    }


def get_installation_guide(part_identifier: str) -> dict:
    part = retrieval.get_part(part_identifier)
    if part is None:
        return {"data": {"found": False, "identifier": part_identifier}, "ui_block": None}
    snippets = retrieval.search_support("how to install replace", part["ps_number"], k=4)
    stories = [s["document"] for s in snippets if s.get("kind") == "story"][:3]
    data = {
        "found": True,
        "ps_number": part["ps_number"],
        "title": part["title"],
        "difficulty": part.get("install_difficulty"),
        "time": part.get("install_time"),
        "video_url": part.get("video_url"),
        "product_url": part.get("product_url"),
        "customer_stories": stories,
    }
    return {
        "data": data,
        "ui_block": {
            "type": "install_guide",
            "part": _card(part),
            "difficulty": data["difficulty"],
            "time": data["time"],
            "video_url": data["video_url"],
            "stories": stories,
        },
    }


# ----------------------------------------------------------- registry/schema

TOOLS = {
    "search_parts": (
        search_parts,
        SearchPartsIn,
        "Search the parts catalog with natural language (hybrid keyword+semantic).",
    ),
    "get_part_details": (
        get_part_details,
        PartDetailsIn,
        "Exact lookup of one part by PS number / manufacturer number / superseded number.",
    ),
    "check_compatibility": (
        check_compatibility,
        CompatibilityIn,
        "Deterministic check whether a part fits an appliance model (database join, never a guess).",
    ),
    "diagnose_issue": (
        diagnose_issue,
        DiagnoseIn,
        "Map a symptom description to likely causes (ranked) and candidate parts.",
    ),
    "get_installation_guide": (
        get_installation_guide,
        InstallGuideIn,
        "Installation difficulty, time, video and real customer repair stories for a part."
    ),
}

FRIENDLY_LABELS = {
    "search_parts": "Searching the catalog…",
    "get_part_details": "Looking up the part…",
    "check_compatibility": "Checking compatibility…",
    "diagnose_issue": "Diagnosing the issue…",
    "get_installation_guide": "Fetching install help…",
}


def openai_tool_schemas() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {"name": name, "description": desc, "parameters": model.model_json_schema()},
        }
        for name, (_, model, desc) in TOOLS.items()
    ]


def run_tool(name: str, arguments: dict) -> dict:
    fn, model, _ = TOOLS[name]
    args = model(**arguments)
    return fn(**args.model_dump())


# ------------------------------------------------- hallucination validator


class HallucinationError(Exception):
    def __init__(self, numbers: set[str]):
        self.numbers = numbers
        super().__init__(f"unverified part numbers in draft: {numbers}")


def validate_part_numbers(text: str, allowed: set[str]) -> None:
    """Final-draft check: every PS number must have appeared in a tool result."""
    mentioned = set(PS_RE.findall(text))
    unverified = mentioned - allowed
    if unverified:
        raise HallucinationError(unverified)
