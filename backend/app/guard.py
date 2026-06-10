"""Layered scope guard: cheap regex fast-path, then a tiny LLM classification.

Defense in depth: this runs BEFORE the agent; the system prompt restates the
rules to catch mid-conversation drift; the eval proves both layers.
"""

from __future__ import annotations

import logging
import random
import re

from backend.app import prompts

logger = logging.getLogger(__name__)

IN_SCOPE_RE = re.compile(
    r"(fridge|refrigerat|freezer|dishwash|dish rack|dishrack|ice maker|icemaker|"
    r"\bPS\d{5,9}\b|part\b|parts\b|model\s*(number|#)?|compatib|install|"
    r"order|return|refund|cancel|warranty|filter|spray arm|drain|gasket|seal|"
    r"shelf|bin|crisper|defrost|compressor|wash|rinse|detergent|leak|noisy|"
    r"\bW(P|D)?[A-Z]?\d{5,}\b|\b[A-Z]{2,4}\d{3,}[A-Z0-9]*\b)",
    re.I,
)

INJECTION_RE = re.compile(
    r"(ignore (all |the |any )?(previous|prior|above|earlier) (instruction|prompt|rule)|"
    r"system prompt|reveal (your|the) (prompt|instruction)|jailbreak|"
    r"pretend (you('| a)?re|to be) (not |no longer )|developer mode|DAN\b|"
    r"disregard (your|the|all) (instruction|rule|guideline))",
    re.I,
)

# explicit fridge/dishwasher mention overrides the other-appliance deflection
CORE_APPLIANCE_RE = re.compile(
    r"(fridge|refrigerat|freezer|dish ?wash|dishrack|ice ?maker|\bPS\d{5,9}\b)", re.I
)

OTHER_APPLIANCE_RE = re.compile(
    r"\b(washer|washing machine|dryer|oven|stove|range|microwave|grill|lawn ?mower|"
    r"chainsaw|air conditioner|furnace|water heater|toaster|blender|coffee)\b",
    re.I,
)


def classify(message: str, history_in_scope: bool = False) -> str:
    """-> 'in_scope' | 'out_of_scope' | 'injection' | 'other_appliance'"""
    if INJECTION_RE.search(message):
        # An injection payload embedded in an otherwise-valid parts question is
        # let through: the system prompt + hallucination gate hold the line, and
        # the agent answers the legitimate part while ignoring the payload.
        if not (CORE_APPLIANCE_RE.search(message)):
            return "injection"
        logger.warning("injection pattern inside in-scope message - passing to agent: %.80s", message)
    if OTHER_APPLIANCE_RE.search(message) and not CORE_APPLIANCE_RE.search(message):
        return "other_appliance"
    if IN_SCOPE_RE.search(message):
        return "in_scope"
    # short follow-ups in an in-scope conversation pass (latency win, no LLM call)
    if history_in_scope and len(message.split()) <= 12:
        return "in_scope"
    return _llm_classify(message)


def _llm_classify(message: str) -> str:
    from backend.app.llm_client import get_client

    label = get_client().classify(prompts.GUARD_CLASSIFIER_PROMPT.format(message=message[:500]))
    if label not in ("in_scope", "out_of_scope", "injection"):
        label = "out_of_scope"
    logger.info("guard llm classification: %s", label)
    return label


def deflection(kind: str) -> str:
    if kind == "injection":
        return prompts.INJECTION_REFUSAL
    if kind == "other_appliance":
        return prompts.OTHER_APPLIANCE_DEFLECTION
    return random.choice(prompts.DEFLECTIONS)
