"""Eval harness: run eval/cases.json against the live backend, write RESULTS.md.

    python eval/run_eval.py [--suite scope] [--case spec_01] [--concurrency 4]

Methodology: each case opens a fresh session and replays its turns through the
streaming /chat API; expectations apply to the final answer. To absorb LLM
nondeterminism a failing case is retried once before being marked failed
(stated in RESULTS.md). The hallucination check is mechanical: every PS number
in the final answer must appear in the case's allowed list, in a tool result's
ui_block, or in the parts catalog (GET /parts/{ps}).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import subprocess
import time
import uuid
from pathlib import Path

import httpx

BASE = "http://localhost:8000"
PS_RE = re.compile(r"PS\d{5,9}")
HERE = Path(__file__).parent


async def stream_chat(client: httpx.AsyncClient, session: str, message: str) -> dict:
    tools, text, deflected, blocks = [], [], None, []
    async with client.stream(
        "POST", f"{BASE}/chat", json={"session_id": session, "message": message}, timeout=120
    ) as resp:
        resp.raise_for_status()
        event = ""
        async for line in resp.aiter_lines():
            line = line.strip()
            if line.startswith("event:"):
                event = line.split(":", 1)[1].strip()
            elif line.startswith("data:") and line != "data:":
                data = json.loads(line.split(":", 1)[1])
                if event == "token":
                    text.append(data["delta"])
                elif event == "tool_start":
                    tools.append(data["name"])
                elif event == "ui_block":
                    blocks.append(data)
                elif event == "done":
                    deflected = data.get("deflected")
    return {"tools": tools, "text": "".join(text), "deflected": deflected, "blocks": blocks}


async def known_ps(client: httpx.AsyncClient, ps: str, cache: dict) -> bool:
    if ps not in cache:
        r = await client.get(f"{BASE}/parts/{ps}")
        cache[ps] = r.status_code == 200
    return cache[ps]


async def run_case(client: httpx.AsyncClient, case: dict, catalog_cache: dict) -> dict:
    exp = case["expect"]
    t0 = time.monotonic()
    session = f"eval-{case['id']}-{uuid.uuid4().hex[:6]}"
    final = {}
    for turn in case["turns"]:
        final = await stream_chat(client, session, turn)
    latency = int((time.monotonic() - t0) * 1000)

    notes: list[str] = []
    answer = final["text"]
    low = answer.lower()

    if "tools_called" in exp:
        want, got = set(exp["tools_called"]), set(final["tools"])
        if want and not want <= got:
            notes.append(f"tools: wanted {sorted(want)} got {sorted(got)}")
        if not want and got:
            notes.append(f"tools: expected none, got {sorted(got)}")
    if exp.get("answer_contains_any") and not any(s.lower() in low for s in exp["answer_contains_any"]):
        notes.append(f"missing any of {exp['answer_contains_any']}")
    for s in exp.get("answer_not_contains", []):
        if s.lower() in low:
            notes.append(f"must not contain {s!r}")
    in_scope = final["deflected"] is None
    if exp.get("must_be_in_scope") is True and not in_scope:
        notes.append("was deflected but should be in scope")
    if exp.get("must_be_in_scope") is False and in_scope:
        notes.append("should have been deflected")

    hallucinated: list[str] = []
    allowed = set(exp.get("allowed_ps_numbers", []))
    for b in final["blocks"]:
        allowed |= set(PS_RE.findall(json.dumps(b)))
    for ps in set(PS_RE.findall(answer)):
        if ps not in allowed and not await known_ps(client, ps, catalog_cache):
            hallucinated.append(ps)
    if exp.get("no_ps_numbers_allowed") and PS_RE.search(answer):
        for ps in set(PS_RE.findall(answer)):
            if ps not in allowed:
                hallucinated.append(ps)
    if hallucinated:
        notes.append(f"HALLUCINATED: {sorted(set(hallucinated))}")

    return {
        "id": case["id"],
        "suite": case["suite"],
        "passed": not notes,
        "latency_ms": latency,
        "notes": "; ".join(notes),
        "hallucinated": sorted(set(hallucinated)),
        "tool_ok": not any(n.startswith("tools:") for n in notes),
        "scope_ok": not any("deflect" in n or "scope" in n for n in notes),
    }


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite")
    ap.add_argument("--case", dest="case_id")
    ap.add_argument("--concurrency", type=int, default=4)
    args = ap.parse_args()

    cases = json.loads((HERE / "cases.json").read_text())
    if args.suite:
        cases = [c for c in cases if c["suite"] == args.suite]
    if args.case_id:
        cases = [c for c in cases if c["id"] == args.case_id]

    sem = asyncio.Semaphore(args.concurrency)
    catalog_cache: dict = {}
    async with httpx.AsyncClient(trust_env=False) as client:
        health = (await client.get(f"{BASE}/health")).json()

        async def guarded(case: dict) -> dict:
            async with sem:
                result = await run_case(client, case, catalog_cache)
                if not result["passed"]:  # one retry for nondeterminism
                    result = await run_case(client, case, catalog_cache)
                    result["notes"] = ("(after retry) " + result["notes"]) if result["notes"] else ""
                return result

        results = await asyncio.gather(*[guarded(c) for c in cases])

    write_results(sorted(results, key=lambda r: r["id"]), health)


def write_results(results: list[dict], health: dict) -> None:
    suites: dict[str, list[dict]] = {}
    for r in results:
        suites.setdefault(r["suite"], []).append(r)
    latencies = sorted(r["latency_ms"] for r in results)
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))]
    total = len(results)
    passed = sum(r["passed"] for r in results)
    hallucinated = sum(len(r["hallucinated"]) for r in results)
    tool_acc = 100 * sum(r["tool_ok"] for r in results) / total
    scope_acc = 100 * sum(r["scope_ok"] for r in results) / total
    sha = subprocess.run(  # noqa: S603 - fixed argv, dev tooling
        ["git", "rev-parse", "--short", "HEAD"],  # noqa: S607
        capture_output=True,
        text=True,
    ).stdout.strip()

    lines = [
        "# Eval Results",
        "",
        f"- **Model:** {health.get('llm_model')}  |  **Date:** {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}  |  **Git:** `{sha}`",
        "- **Methodology:** every case replays its turns through the live SSE `/chat` API in a fresh session; "
        "a failing case is retried once (LLM nondeterminism) before being marked failed.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Overall pass rate | **{passed}/{total} ({100 * passed / total:.0f}%)** |",
        f"| Tool-selection accuracy | {tool_acc:.0f}% |",
        f"| Scope adherence | {scope_acc:.0f}% |",
        f"| Hallucinated part numbers | **{hallucinated}** |",
        f"| Latency p50 / p95 | {p50} ms / {p95} ms |",
        "",
        "| Suite | Passed |",
        "|---|---|",
    ]
    for suite, rs in sorted(suites.items()):
        lines.append(f"| {suite} | {sum(r['passed'] for r in rs)}/{len(rs)} |")
    lines += [
        "",
        "## Per-case results",
        "",
        "| Case | Suite | Result | Latency | Note |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['id']} | {r['suite']} | {'✅' if r['passed'] else '❌'} | "
            f"{r['latency_ms']} ms | {r['notes'] or ''} |"
        )
    (HERE / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:20]))
    print(f"\nwrote eval/RESULTS.md  ({passed}/{total} passed, {hallucinated} hallucinations)")


if __name__ == "__main__":
    asyncio.run(main())
