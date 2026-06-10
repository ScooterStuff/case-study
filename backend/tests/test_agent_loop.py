"""Agent loop mechanics with scripted LLM clients."""

from __future__ import annotations

import asyncio
import json
import uuid


def _events(monkeypatch, client, message="my fridge part please"):
    from backend.app import agent as agent_mod

    monkeypatch.setattr(agent_mod, "get_client", lambda: client)

    async def collect():
        out = []
        async for ev in agent_mod.chat_stream(f"t-{uuid.uuid4().hex[:6]}", message):
            out.append(ev)
        return out

    return asyncio.get_event_loop().run_until_complete(collect())


class EndlessToolCaller:
    """Always asks for another tool - loop must stop at MAX_TOOL_ROUNDS."""

    def __init__(self):
        self.rounds = 0

    async def chat(self, messages, tools):
        self.rounds += 1
        yield (
            "tool_calls",
            [
                {
                    "id": f"c{self.rounds}",
                    "name": "get_part_details",
                    "arguments": {"part_identifier": "PS11752778"},
                }
            ],
        )

    def classify(self, prompt):
        return "in_scope"


def test_loop_terminates_at_max_rounds(monkeypatch) -> None:
    from backend.app.agent import MAX_TOOL_ROUNDS

    client = EndlessToolCaller()
    events = _events(monkeypatch, client)
    assert client.rounds == MAX_TOOL_ROUNDS + 1
    assert events[-1]["event"] == "done"


class ParallelCaller:
    """Two tool calls in one round - both must execute, then a final answer."""

    def __init__(self):
        self.called = 0

    async def chat(self, messages, tools):
        if self.called == 0:
            self.called += 1
            yield (
                "tool_calls",
                [
                    {"id": "a", "name": "get_part_details", "arguments": {"part_identifier": "PS11752778"}},
                    {"id": "b", "name": "get_part_details", "arguments": {"part_identifier": "PS3406971"}},
                ],
            )
        else:
            yield ("token", "Both parts found: PS11752778 and PS3406971.")

    def classify(self, prompt):
        return "in_scope"


def test_parallel_tools_and_event_order(monkeypatch) -> None:
    events = _events(monkeypatch, ParallelCaller())
    kinds = [e["event"] for e in events]
    assert kinds.count("tool_start") == 2 and kinds.count("tool_end") == 2
    # ordering: all tool events precede the first token; done is last
    assert max(i for i, k in enumerate(kinds) if k == "tool_end") < kinds.index("token")
    assert kinds[-1] == "done"
    text = "".join(e["data"]["delta"] for e in events if e["event"] == "token")
    assert "PS11752778" in text  # validated: numbers came from tool results


class CrashingToolCaller:
    def __init__(self):
        self.calls = 0

    async def chat(self, messages, tools):
        if self.calls == 0:
            self.calls += 1
            yield (
                "tool_calls",
                [
                    {
                        "id": "x",
                        "name": "diagnose_issue",
                        "arguments": {"symptom_description": "leak", "appliance_type": "submarine"},
                    }
                ],
            )
        else:
            # the loop must hand the tool error back to the LLM, not crash
            last = messages[-1]
            assert last["role"] == "tool" and "error" in last["content"]
            yield ("token", "Sorry, I hit a snag with that one.")

    def classify(self, prompt):
        return "in_scope"


def test_tool_error_surfaced_not_crashing(monkeypatch) -> None:
    events = _events(monkeypatch, CrashingToolCaller())
    assert events[-1]["event"] == "done"
    text = "".join(e["data"]["delta"] for e in events if e["event"] == "token")
    assert "snag" in text


def test_history_compaction_truncates_long_fields() -> None:
    from backend.app.agent import _compact

    blob = {"data": {"big": "x" * 5000, "list": list(range(50)), "ok": 1}, "ui_block": None}
    compacted = json.loads(_compact(blob))  # stays valid JSON
    assert len(compacted["data"]["big"]) <= 400
    assert len(compacted["data"]["list"]) <= 6
