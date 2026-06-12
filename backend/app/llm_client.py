"""LLM access: an OpenAI-compatible streaming client, plus a scripted MOCK
client (MOCK_LLM=1) used by CI, docker demo mode, and keyless development.

Both expose:
    async chat(messages, tools) -> yields ("token", str) and finally
                                   ("tool_calls", list) when tools are invoked
    classify(prompt) -> str       tiny sync call for the scope guard
"""

from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator
from typing import Any

from backend.app import config
from backend.app.appliances import ALL_KEYWORDS, APPLIANCES, KEYWORDS, display_list

# Appliance detection for MockLLM is derived from appliances.toml — adding a
# new appliance there (name + keywords) auto-extends the mock router, the
# bare-appliance clarifier, and the closing line. Internal whitespace in a
# keyword is treated as optional, so 'dish rack' matches 'dishrack' too.
def _kw_pattern(kw: str) -> str:
    parts = re.split(r"\s+", kw.strip())
    return r"\s*".join(re.escape(p) for p in parts)


_APPLIANCE_REGEXES: dict[str, re.Pattern[str]] = {
    name: re.compile("|".join(_kw_pattern(k) for k in kws), re.I) for name, kws in KEYWORDS.items()
}
_APPLIANCE_WORDS: frozenset[str] = frozenset(
    {a.lower() for a in APPLIANCES} | {k.lower() for k in ALL_KEYWORDS}
)


def _detect_appliance(text: str) -> str | None:
    """Return the canonical appliance name whose keywords first match `text`."""
    for name, rx in _APPLIANCE_REGEXES.items():
        if rx.search(text):
            return name
    return None


class RealLLM:
    def __init__(self) -> None:
        from openai import AsyncOpenAI, OpenAI

        self._async = AsyncOpenAI(base_url=config.settings.llm_base_url, api_key=config.settings.llm_api_key)
        self._sync = OpenAI(base_url=config.settings.llm_base_url, api_key=config.settings.llm_api_key)

    async def chat(self, messages: list[dict], tools: list[dict]) -> AsyncIterator[tuple[str, Any]]:
        stream = await self._async.chat.completions.create(
            model=config.settings.llm_model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            stream=True,
            temperature=0.2,
        )
        calls: dict[int, dict] = {}
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue
            if delta.content:
                yield ("token", delta.content)
            for tc in delta.tool_calls or []:
                slot = calls.setdefault(tc.index, {"id": "", "name": "", "arguments": ""})
                slot["id"] = tc.id or slot["id"]
                if tc.function:
                    slot["name"] = tc.function.name or slot["name"]
                    slot["arguments"] += tc.function.arguments or ""
        if calls:
            yield (
                "tool_calls",
                [
                    {"id": c["id"], "name": c["name"], "arguments": json.loads(c["arguments"] or "{}")}
                    for c in calls.values()
                ],
            )

    def classify(self, prompt: str) -> str:
        resp = self._sync.chat.completions.create(
            model=config.settings.llm_model,
            max_tokens=8,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        return (resp.choices[0].message.content or "").strip().lower()


PS_RE = re.compile(r"PS\d{5,9}", re.I)
MPN_RE = re.compile(r"\b(?=[A-Z0-9\-]*\d)(?=[A-Z0-9\-]*[A-Z])[A-Z][A-Z0-9\-]{5,14}\b")
MODEL_HINT_RE = re.compile(r"\bmodel(?:\s*(?:number|#|no\.?))?\s*(?:is\s*)?([A-Za-z0-9\-]{5,})", re.I)


class MockLLM:
    """Deterministic, tool-faithful scripted 'LLM'.

    Routes the user's message to the right tool, then writes the final answer
    *only* from values present in tool results - mirroring what the system
    prompt demands of the real model. Good enough to demo the full UX and run
    e2e/CI with zero keys; NOT a language model.
    """

    async def chat(self, messages: list[dict], tools: list[dict]) -> AsyncIterator[tuple[str, Any]]:
        last = messages[-1]
        if last["role"] == "tool":
            text = self._final_text(messages)
            for i in range(0, len(text), 24):
                yield ("token", text[i : i + 24])
            return
        call = self._route(messages)
        if call is not None:
            yield ("tool_calls", [call])
            return
        text = self._clarifier_text(messages)
        for i in range(0, len(text), 24):
            yield ("token", text[i : i + 24])

    @staticmethod
    def _clarifier_text(messages: list[dict]) -> str:
        """Context-aware fallback when no tool fires (mock-mode UX polish).

        A real LLM would carry context naturally; in MOCK mode, give short
        conversational follow-ups ('yes', 'refrigerator') a useful next-step
        instead of looping the same generic prompt.
        """
        msg = messages[-1].get("content", "").strip().lower().rstrip("!?.,")
        prior = next(
            (
                m["content"]
                for m in reversed(messages[:-1])
                if m.get("role") == "assistant" and m.get("content")
            ),
            "",
        ).lower()
        if re.fullmatch(r"(yes|yeah|yep|yup|sure|please|ok+|okay|y)", msg):
            if "fits your model" in prior or "verify the right part" in prior:
                return (
                    "Great - what's your model number? It's usually on a sticker "
                    "inside the door, on the side wall, or behind the kick plate."
                )
            if "install help" in prior or "step-by-step" in prior:
                return "Sure - share the part number and I'll pull the install steps."
            return (
                "Got it - what would you like to do next? A part number, model number, or a symptom all work."
            )
        if msg in _APPLIANCE_WORDS:
            which = _detect_appliance(msg) or msg
            return f"Got it - a {which}. What's it doing? A symptom, part number, or model number all work."
        return (
            f"Happy to help! Which appliance is acting up - your "
            f"{display_list(' or ')} - and what is it doing? A part number or "
            "model number works too."
        )

    def classify(self, prompt: str) -> str:
        from backend.app.guard import IN_SCOPE_RE, INJECTION_RE

        msg = prompt.rsplit("Message:", 1)[-1]
        if INJECTION_RE.search(msg):
            return "injection"
        if IN_SCOPE_RE.search(msg):
            return "in_scope"
        return "out_of_scope"

    # ------------------------------------------------------------- routing

    def _route(self, messages: list[dict]) -> dict | None:
        msg = messages[-1]["content"]
        low = msg.lower()
        ps_numbers = [m.upper() for m in PS_RE.findall(msg)]
        ps = ps_numbers[0] if ps_numbers else None

        def hist_text() -> str:
            return " ".join(str(m.get("content", "")) for m in messages[:-1] if m.get("role") != "system")

        if not ps and re.search(r"\b(this|that|the) part\b", low):
            prev = PS_RE.findall(hist_text())
            ps = prev[-1].upper() if prev else None

        appliance = _detect_appliance(low) or _detect_appliance(hist_text())

        model = None
        m = MODEL_HINT_RE.search(msg)
        if m and not PS_RE.fullmatch(m.group(1).upper()):
            model = m.group(1).upper()
        if model is None:
            cands = [c for c in MPN_RE.findall(msg.upper()) if not c.startswith("PS")]
            if re.search(r"compatib|fit", low) and cands:
                model = cands[-1]
        if model is None and re.search(r"compatib|\bfits?\b", low):
            m2 = re.search(r"(?:with|fit)s? my ([a-z0-9][a-z0-9 \-]{4,})[\?\.!]?$", low)
            if m2:
                cand = re.sub(r"[^a-z0-9]", "", m2.group(1)).upper()
                if re.search(r"\d", cand) and not cand.startswith("PS"):
                    model = cand

        if re.search(r"compatib|\bfits?\b", low) and (ps or model):
            if ps and model:
                return self._call("check_compatibility", part_identifier=ps, model_number=model)
            if model:
                prev = PS_RE.findall(hist_text())
                if prev:
                    return self._call(
                        "check_compatibility", part_identifier=prev[-1].upper(), model_number=model
                    )
        if re.search(r"install|how (do|can) i (put|replace|fit)|replace", low) and ps:
            return self._call("get_installation_guide", part_identifier=ps)
        if ps:
            return self._call("get_part_details", part_identifier=ps)
        if re.search(r"\bpart\b|\bnumber\b|tell me about", low):
            cands = [c for c in MPN_RE.findall(msg.upper()) if not c.startswith("PS") and c != (model or "")]
            if cands:
                return self._call("get_part_details", part_identifier=cands[0])
        if appliance and re.search(
            r"not work|won'?t|isn'?t|broken|leak|nois|too warm|too cold|"
            r"not (mak|clean|drain|dry|start|dispens)|stopped|problem|fix",
            low,
        ):
            return self._call(
                "diagnose_issue", symptom_description=msg, appliance_type=appliance, brand=self._brand(low)
            )
        if re.search(r"\bneed\b|\bfind\b|looking for|\bsearch\b|\bthing\b|recommend|\bbuy\b", low):
            return self._call("search_parts", query=msg, appliance_type=appliance)
        return None

    @staticmethod
    def _brand(low: str) -> str | None:
        for b in (
            "whirlpool",
            "ge",
            "samsung",
            "lg",
            "bosch",
            "frigidaire",
            "kitchenaid",
            "kenmore",
            "maytag",
        ):
            if re.search(rf"\b{b}\b", low):
                return b.capitalize()
        return None

    @staticmethod
    def _call(name: str, **arguments: Any) -> dict:
        return {
            "id": f"mock-{name}",
            "name": name,
            "arguments": {k: v for k, v in arguments.items() if v is not None},
        }

    # ------------------------------------------------------ final answers

    def _final_text(self, messages: list[dict]) -> str:
        tool_msg = messages[-1]
        name = tool_msg.get("name", "")
        data = json.loads(tool_msg["content"]).get("data", {})
        if name == "get_installation_guide":
            if not data.get("found"):
                return (
                    f"I couldn't find part {data.get('identifier')} in our catalog - "
                    "could you double-check the number?"
                )
            bits = [
                f"Installing the {data['title']} ({data['ps_number']}) is rated "
                f'"{data.get("difficulty") or "Easy"}"'
            ]
            if data.get("time"):
                bits.append(f"and typically takes {data['time']}")
            text = " ".join(bits) + "."
            if data.get("customer_stories"):
                text += f' One customer put it this way: "{data["customer_stories"][0][:160]}".'
            if data.get("video_url"):
                text += f" There's a step-by-step video here: {data['video_url']}"
            text += " Want me to check it fits your model before you order?"
            return text
        if name == "check_compatibility":
            s, model, part = data["status"], data["model_number"], data["ps_number"]
            if s == "verified_fit":
                return (
                    f"Yes - {part} is a verified fit for model {model} per PartSelect's "
                    "cross-reference data. Want install help?"
                )
            if s == "no_match_found":
                extra = ""
                if data.get("parts_verified_for_model_sample"):
                    extra = (
                        " For that model we do have verified parts like: "
                        + "; ".join(data["parts_verified_for_model_sample"][:3])
                        + "."
                    )
                return (
                    f"{part} is not in our verified compatibility list for model {model} "
                    f"({data['evidence'].get('part_appliance', '')} part vs. your model), so I "
                    f"can't confirm a fit.{extra} Want me to look for the right equivalent?"
                )
            if s == "unknown_model":
                return (
                    f"I couldn't find model {model} in our data - model numbers are usually on a "
                    "sticker inside the door or frame. Could you double-check it?"
                )
            return f"I couldn't find part {part} in our catalog - could you double-check the number?"
        if name == "diagnose_issue":
            causes = data.get("causes", [])
            parts = data.get("suggested_parts", [])
            if not causes:
                return "I couldn't match that symptom to a known repair guide. Could you describe what's happening?"
            lines = ["Here's the most likely diagnosis, in order of likelihood:"]
            for c in causes[:4]:
                lines.append(f"{c['rank']}. {c['cause']}")
            if parts:
                p = parts[0]
                price = f" (${p['price']:.2f}, {p['availability']})" if p.get("price") else ""
                lines.append(f"A common fix is the {p['title']} - {p['ps_number']}{price}.")
            lines.append("Tell me your model number and I'll verify the right part fits before you order.")
            return "\n".join(lines)
        if name == "get_part_details":
            if not data.get("found"):
                return (
                    f"I couldn't find part {data.get('identifier')} in our catalog - could you "
                    "double-check the number? It usually starts with PS."
                )
            price = f"${data['price']:.2f}" if data.get("price") else "price unavailable"
            return (
                f"{data['title']} ({data['ps_number']}, mfr # {data['mpn']}) by {data['brand']} - "
                f"{price}, {data.get('availability', '')}. Rated "
                f'"{data.get("install_difficulty") or "Easy"}" to install. Want me to check it '
                "fits your model?"
            )
        if name == "search_parts":
            results = data.get("results", [])
            if not results:
                return "I didn't find a matching part. Could you describe it differently or share your model number?"
            lines = ["Here's what I found:"]
            for p in results[:3]:
                price = f" - ${p['price']:.2f}" if p.get("price") else ""
                lines.append(f"• {p['title']} ({p['ps_number']}){price}, {p.get('availability', '')}")
            lines.append("Share your model number and I'll confirm which one fits.")
            return "\n".join(lines)
        return f"Done - anything else {display_list(' or ')}-related I can help with?"


def get_client():
    return MockLLM() if config.settings.mock_llm else RealLLM()
