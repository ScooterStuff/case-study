# Loom script — technical deep-dive deck

Audience already knows the product; this is about design choices and
implementation. ~8–9 min of slides, then the live demo. Stage directions in
*italics*.

---

## Slide 1 — Title (~20s)

> Hi, I'm Tatsan. You've seen what the PartSelect agent does — this walkthrough
> is about how it's built: the interface engineering, the agentic architecture,
> how it's grounded, and how it extends and scales. I'll close with a live demo.

## Slide 2 — System architecture (~45s)

> Here's the full system. Three properties to notice, because everything else
> follows from them. First: one database, two retrieval substrates — relational
> tables for facts, pgvector for semantics, which means a semantic hit can JOIN
> price and stock in the same query. Second: the LLM is surrounded, not
> trusted — a guard in front of it, typed tools beside it, and a mechanical
> validator behind it. And third: the whole thing runs keyless — committed
> seed data plus a scripted mock LLM means CI, end-to-end tests, and demos
> need zero API keys.

## Slide 3 — Anatomy of one chat turn (~45s)

> This is the runtime of a single turn. The design idea is buffer-and-release:
> tool status events and rich UI blocks stream to the browser immediately, but
> the final prose is held for about a hundred milliseconds while the
> hallucination gate checks it. Users see instant activity; invented part
> numbers can never reach the screen.
>
> Two more details: independent tool calls fan out in parallel with
> asyncio.gather, and a tool failure becomes a `tool_error` event the agent
> recovers from conversationally — never a 500. And tool results enter history
> JSON-safe-trimmed, so context stays bounded no matter how long the
> conversation runs.

## Slide 4 — The agent loop (~50s)

> Here's the loop itself, distilled from agent.py. It's deliberately a single
> agent: at this scale, multi-agent buys you latency, failure modes, and
> un-evaluatable behavior. The abstraction that earns its keep is the tool
> registry.
>
> Notice what's bounded by construction — at most four tool rounds, twenty
> history messages, trimmed payloads. No unbounded loops. The session store is
> an in-memory dict behind one accessor, which is a deliberate swap point for
> Redis. And `llm.chat()` is an interface with two implementations — an
> OpenAI-compatible streaming client and a scripted mock that honors the same
> contract, which is what makes the whole system testable without keys.

## Slide 5 — Scope control (~40s)

> Scope control is layered, cheap to expensive. A regex fast-path passes
> obvious parts traffic in microseconds — that's why time-to-first-event under
> 1.5 seconds is a tested invariant, not a hope. Only ambiguous messages pay
> for a classifier call, and it's capped at eight tokens. The system prompt is
> layer three, for mid-conversation drift.
>
> One design call worth defending: when an injection payload is embedded
> inside a legitimate parts question, the guard doesn't refuse the whole
> message — it answers the real question and ignores the payload, because the
> deeper layers make that safe. The eval's injection suite proves it.

## Slide 6 — Grounding (~45s)

> Grounding is the part I'd push back on hardest if someone called it a prompt
> trick — it isn't one. The validator is mechanical: every part number in the
> final draft must exist in this conversation's tool results, or in what the
> user themselves typed — because "I couldn't find PS99999999" has to be
> sayable. On a violation it retries once with a corrective nudge, then strips
> the number and logs the incident to a JSONL audit file.
>
> It's tested with a deliberately lying LLM in the unit suite. And honesty
> goes deeper than the gate: compatibility verdicts are a four-state enum with
> evidence counts, so "not in our verified list" is data-layer truth, not
> prompt wording.

## Slide 7 — Data layer (~40s)

> The schema is small and deliberate. Raw parameterized SQL, no ORM — there
> are about ten queries and they ARE the architecture. The money query is the
> compatibility JOIN at the bottom. Around it: supersession resolution, so a
> ten-year-old manufacturer number still lands on the current part; provenance
> on every compatibility row, so weaker signals like Q&A-harvested fits are
> distinguishable; and a committed pg_dump seed that restores with psycopg
> alone — first container boot self-heals.

## Slide 8 — Hybrid search (~40s)

> Search is hybrid because either half alone fails half the queries: exact
> tokens like a manufacturer number need keyword search; "the thing that
> sprays water in the bottom" needs vectors. The merge is reciprocal rank
> fusion — chosen because keyword and cosine scores live on incomparable
> scales, and RRF needs no calibration and degrades gracefully when one side
> returns nothing. Both branches are appliance-scoped, and even the embeddings
> are env-swappable, with a deterministic mock so every vector code path runs
> in keyless CI.

## Slide 9 — The SSE contract (~40s)

> The frontend is intentionally thin: a renderer for a typed event stream. Six
> event types — that table is the entire contract. The ui_block payload shapes
> are defined once in tools.py and mirrored as typedefs on the client, so
> there's one source of truth. The SSE parser is hand-rolled over fetch and
> ReadableStream, and its unit tests split events mid-JSON and mid-event-name
> to prove reassembly. And block buttons emit templated chat messages — the
> product cards are conversation controls, so there's no parallel routing
> system to maintain.

## Slide 10 — Photo → model number (~50s)

> The newest piece. Model stickers are genuinely hard to transcribe, so the
> composer accepts a photo of one — and the whole pipeline is client-side.
> Tesseract.js does OCR in the browser, lazy-loaded so its three megabytes are
> only paid when someone actually taps the camera. The interesting engineering
> is the extractor: a pure function that tiers candidate tokens — long numeric
> runs for Kenmore-style models, letter-digit mixes for Whirlpool and GE —
> while rejecting stopwords, years, and noise. Pure means Jest-testable
> without any OCR in the loop.
>
> Then the handoff is context-aware: if a part is already in the conversation,
> the detected model prefills as a compatibility question; otherwise as a
> parts search. And because nothing leaves the device, there's no upload
> endpoint, no vision-API cost, and no privacy surface.

## Slide 11 — Extensibility & scalability (~45s)

> Extension points are proven, not promised — the order-support tool was
> actually deleted, and the change touched the registry only; the loop, the
> protocol, and the UI never knew. A new appliance is scraper seeds plus an
> enum value. The provider swaps with env vars. A new rich block is one tool
> payload and one React component.
>
> Scaling follows a deliberate order: sessions to Redis — a one-class change —
> then horizontal replicas behind the existing nginx; Postgres carries both
> workloads to about a million embeddings before a dedicated vector store is
> even a conversation; and observability is already structured — request-id
> middleware and per-turn JSON logs, so production telemetry is an exporter,
> not a rewrite.

## Slide 12 — Quality, then demo (~30s)

> Quality is two separate layers: tests prove the code — 91% backend coverage
> with an 80% CI gate, twenty frontend tests including the OCR extractor — and
> evals prove the agent: forty multi-turn conversations replayed through the
> live API, zero hallucinated part numbers, with the methodology published.
> The harness caught two real routing bugs during development.
>
> That's the engineering. Now let me show you the product — watch for the
> streaming tool pills, the photo flow, and an honest compatibility verdict.

*(Switch to the live demo.)*
