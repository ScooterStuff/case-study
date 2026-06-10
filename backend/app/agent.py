"""The agent loop: guard -> LLM -> tools -> validated, streamed answer.

One orchestrating LLM with six tools (no multi-agent) - lower latency, simpler
failure modes, easier evals; extensibility lives in the tool registry.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from backend.app import guard, prompts
from backend.app.llm_client import get_client
from backend.app.tools import (
    FRIENDLY_LABELS,
    PS_RE,
    HallucinationError,
    openai_tool_schemas,
    run_tool,
    validate_part_numbers,
)

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 4
MAX_HISTORY_MESSAGES = 20
HALLUCINATION_LOG = Path(__file__).resolve().parents[1] / "data" / "hallucination_log.jsonl"

# In-memory session store - swap for Redis in production (README notes this).
_sessions: dict[str, dict[str, Any]] = {}


def _session(session_id: str) -> dict[str, Any]:
    return _sessions.setdefault(session_id, {"messages": [], "allowed_ps": set(), "in_scope": False})


def reset_sessions() -> None:
    _sessions.clear()


def _trim(value, max_str=400, max_list=6):
    if isinstance(value, str):
        return value[:max_str]
    if isinstance(value, list):
        return [_trim(v, max_str, max_list) for v in value[:max_list]]
    if isinstance(value, dict):
        return {k: _trim(v, max_str, max_list) for k, v in value.items()}
    return value


def _compact(result: dict) -> str:
    """Tool results go into history compacted (JSON-safe trim, not a byte chop)."""
    return json.dumps(_trim(result), default=str)


async def chat_stream(session_id: str, user_message: str) -> AsyncIterator[dict]:
    """Yields SSE-ready events: token / tool_start / tool_end / ui_block / done."""
    t0 = time.monotonic()
    state = _session(session_id)
    label = guard.classify(user_message, history_in_scope=state["in_scope"])

    if label != "in_scope":
        text = guard.deflection(label)
        state["messages"] += [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": text},
        ]
        for chunk in re.findall(r".{1,40}", text, re.S):
            yield {"event": "token", "data": {"delta": chunk}}
        yield {
            "event": "done",
            "data": {"latency_ms": int((time.monotonic() - t0) * 1000), "deflected": label},
        }
        return

    state["in_scope"] = True
    state["allowed_ps"] |= {m.upper() for m in PS_RE.findall(user_message)}
    state["messages"].append({"role": "user", "content": user_message})

    client = get_client()
    messages = [{"role": "system", "content": prompts.SYSTEM_PROMPT}] + state["messages"][
        -MAX_HISTORY_MESSAGES:
    ]
    final_text = ""

    for _round in range(MAX_TOOL_ROUNDS + 1):
        buffered: list[str] = []  # final prose is buffered for validation
        tool_calls: list[dict] = []
        async for kind, payload in client.chat(messages, openai_tool_schemas()):
            if kind == "token":
                buffered.append(payload)
            elif kind == "tool_calls":
                tool_calls = payload

        if not tool_calls:
            final_text = "".join(buffered)
            break

        if buffered:  # text alongside tool calls: keep in history
            messages.append({"role": "assistant", "content": "".join(buffered)})

        messages.append(
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": c["id"],
                        "type": "function",
                        "function": {"name": c["name"], "arguments": json.dumps(c["arguments"])},
                    }
                    for c in tool_calls
                ],
            }
        )

        for call in tool_calls:
            yield {
                "event": "tool_start",
                "data": {"name": call["name"], "label": FRIENDLY_LABELS.get(call["name"], "Working…")},
            }

        async def _run(call: dict) -> dict:
            try:
                return await asyncio.to_thread(run_tool, call["name"], call["arguments"])
            except Exception as exc:  # noqa: BLE001 - tool errors go back to the LLM
                logger.warning("tool %s failed: %s", call["name"], exc)
                return {"data": {"error": str(exc)}, "ui_block": None}

        results = await asyncio.gather(*[_run(c) for c in tool_calls])

        for call, result in zip(tool_calls, results, strict=True):
            state["allowed_ps"] |= set(PS_RE.findall(json.dumps(result["data"], default=str)))
            yield {"event": "tool_end", "data": {"name": call["name"]}}
            if result.get("ui_block"):
                yield {"event": "ui_block", "data": result["ui_block"]}
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "name": call["name"],
                    "content": _compact(result),
                }
            )

    # ---- hallucination gate: buffer-and-release (tool events streamed live,
    # final prose held briefly; tradeoff: tiny perceived delay vs. zero
    # unverified part numbers ever reaching the user).
    try:
        validate_part_numbers(final_text, state["allowed_ps"])
    except HallucinationError as err:
        _log_hallucination(session_id, user_message, final_text, err.numbers)
        messages.append(
            {"role": "system", "content": prompts.HALLUCINATION_NUDGE.format(numbers=", ".join(err.numbers))}
        )
        retry: list[str] = []
        async for kind, payload in client.chat(messages, openai_tool_schemas()):
            if kind == "token":
                retry.append(payload)
        final_text = "".join(retry) or final_text
        try:
            validate_part_numbers(final_text, state["allowed_ps"])
        except HallucinationError as err2:  # strip and caveat - never ship invented numbers
            for n in err2.numbers:
                final_text = final_text.replace(n, "[part number removed - unverified]")
            final_text += "\n\n(I removed a part number I couldn't verify against our catalog.)"

    state["messages"].append({"role": "assistant", "content": final_text})
    for chunk in re.findall(r".{1,40}", final_text, re.S):
        yield {"event": "token", "data": {"delta": chunk}}
    yield {"event": "done", "data": {"latency_ms": int((time.monotonic() - t0) * 1000)}}


def _log_hallucination(session_id: str, user: str, draft: str, numbers: set[str]) -> None:
    HALLUCINATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with HALLUCINATION_LOG.open("a", encoding="utf-8") as fh:
        fh.write(
            json.dumps(
                {
                    "ts": time.time(),
                    "session": session_id,
                    "user": user,
                    "numbers": sorted(numbers),
                    "draft": draft[:500],
                }
            )
            + "\n"
        )
    logger.error("HALLUCINATION blocked: %s", numbers)
