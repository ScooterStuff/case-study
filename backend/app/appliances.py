"""Single source of truth for in-scope appliances (loaded from appliances.toml).

The TOML is the extension point: add an appliance there, add seed URLs in
``scraper/seeds.py``, re-ingest, and the guard, the Pydantic tool schema, and
the system prompt all pick it up — no other code changes required.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import tomllib

_PATH = Path(__file__).parent / "appliances.toml"
_DATA = tomllib.loads(_PATH.read_text(encoding="utf-8"))

APPLIANCES: tuple[str, ...] = tuple(a["name"] for a in _DATA["appliances"])
KEYWORDS: dict[str, list[str]] = {a["name"]: list(a["keywords"]) for a in _DATA["appliances"]}
ALL_KEYWORDS: tuple[str, ...] = tuple(sorted({k for kws in KEYWORDS.values() for k in kws}))

# Pydantic Literal built at import time from the TOML. ``Literal[tuple]`` is
# accepted as equivalent to the spread form (Literal[a, b]) — the tool JSON
# schema sent to the LLM thus reflects the configured set automatically.
ApplianceType = Literal[APPLIANCES]  # type: ignore[valid-type]


def display_list(joiner: str = " and ") -> str:
    """Human-readable list, e.g. 'refrigerator and dishwasher'."""
    return joiner.join(APPLIANCES)
