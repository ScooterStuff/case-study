# Loom script — slide by slide

Target: 7–9 minutes. Conversational, not read word-for-word. Stage directions
in *italics*. Suggested structure: slides 1–3 → **live demo** → slides 4–11.

---

## Slide 1 — Title (~25s)

> Hi, I'm Tatsan, and this is my Instalily case study: a chat agent for
> PartSelect, scoped to refrigerator and dishwasher parts. The one-line pitch is
> on the slide: it takes a customer from a symptom to a verified, in-cart part —
> and the key word is *measured*. Forty eval cases, zero hallucinated part
> numbers, real scraped data. Let me show you how I got there.

## Slide 2 — Read the spec like an evaluator (~40s)

> Before writing any code I asked: how does this actually get graded? Whoever
> evaluates this will open the app and type these three example queries first.
> So I treated them as acceptance tests — they were written into an automated
> eval before the backend existed, and they're seeded as suggestion chips in
> the UI.
>
> And the strategy follows from that: every candidate ships a branded chat box
> with an LLM and a few tools. The differentiator isn't more features — it's
> *proof*. A measured agent, honest about its data, that a grader can verify in
> five minutes.

## Slide 3 — The trap (~50s) ← spend time here

> Here's my favorite discovery, and it reshaped the whole architecture. I pulled
> the real PartSelect pages for the example queries, and it turns out
> PS11752778 — the part in query one — is a *refrigerator door shelf bin*. But
> query two asks if it's compatible with WDT780SAEM1, which is a *dishwasher*
> model.
>
> So query two is a hallucination trap, intentional or not. The correct answer
> is "that's not a verified fit" — and any agent that cheerfully says "yes,
> compatible!" is making things up. That one fact dictated my core design rule:
> compatibility is a database join. Never an LLM guess.

*(Optional: cut to the live demo here — run the three spec queries, show the
honest ⚠ verdict on query 2, the ranked diagnosis on query 3, then add to cart.
Then come back to slide 4.)*

## Slide 4 — Architecture (~45s)

> The architecture is deliberately simple: one tool-calling LLM, not a
> multi-agent system — at this scale that means lower latency, simpler failure
> modes, and much easier evals. Extensibility lives in the tool registry
> instead.
>
> A message hits the scope guard first — a regex fast-path that costs nothing
> for obvious parts questions, with a tiny classifier only for ambiguous ones.
> The agent then orchestrates six tools over one Postgres database. And at the
> bottom, in red, the part I'm proudest of: a hallucination validator that gates
> the final draft before any token reaches the user. Every part number must
> trace back to a tool result — or it gets stripped.

## Slide 5 — Facts vs. fuzz (~40s)

> The data layer split makes the honesty possible. Anything dangerous to
> hallucinate — prices, stock, compatibility — lives in relational tables and is
> answered by deterministic SQL. Anything fuzzy — "the thing that sprays water
> in the bottom of my dishwasher" — goes through RAG over pgvector embeddings.
>
> Both live in *one* database, so a semantic hit can JOIN price and stock in a
> single query. And notice the honesty baked into the verdict enum:
> PartSelect's cross-reference pages are paginated, so my data is partial — a
> miss is reported as "not in our verified list," never a hard "incompatible."

## Slide 6 — Data pipeline (~35s)

> The data is real, scraped politely: on-disk cache, two-and-a-half-second
> delays, a hard page cap — re-running the scraper makes zero network calls,
> and that's unit-tested. The parser reads the site's own structure:
> schema.org microdata, cross-reference tables, repair causes in PartSelect's
> own likelihood order.
>
> And everything ships as a committed seed — a fresh clone runs with no
> scraping and no API keys. First boot self-heals the database.

## Slide 7 — The eval (~45s)

> This is the slide I'd want you to remember. Forty multi-turn cases replayed
> through the live streaming API — not unit tests, the actual agent. Tool
> selection, answer content, scope behavior, and a mechanical hallucination
> check. Forty out of forty, zero hallucinated part numbers, one hundred
> percent scope adherence.
>
> My favorite case: "just guess whether it fits — yes or no?" The agent refuses
> to guess. And the harness earned its keep — it caught two real routing bugs
> before any human tester would have. Evals measure whether the *agent* is
> right; tests measure whether the *code* is correct. The repo ships both.

## Slide 8 — UX (~35s)

> On the frontend I designed for one person: someone stressed, with a broken
> appliance. They get one continuous path — symptom, diagnosis, the right part,
> verify it fits *their* model, install help, cart. Every tool returns a rich
> block that renders mid-stream, and the card buttons send chat messages — so
> the conversation *is* the navigation. The branding tokens are lifted straight
> from PartSelect's real CSS.

## Slide 9 — Trade-offs (~35s)

> A few deliberate trade-offs, each logged in an ADR-style file in the repo.
> One Postgres for facts and vectors instead of a separate vector DB. Raw SQL
> instead of an ORM — ten queries, and the SQL *is* the architecture demo.
> A single agent instead of multi-agent. Buffering the final prose for about a
> hundred milliseconds to get a mechanical zero-hallucination guarantee. And a
> scripted mock-LLM mode so CI and demos run with zero keys.

## Slide 10 — Extensibility & limits (~30s)

> Extensibility is concrete, not aspirational: a new appliance is seed URLs plus
> one enum value. Real order support is swapping one mocked function body — the
> schema is already the contract. The LLM provider swaps with three env vars.
>
> And I'll name my own limitations: the compatibility data is partial because
> the source paginates, the catalog is a 34-part slice the scraper can scale,
> and orders are mocked. Knowing exactly what you shipped is part of the job.

## Slide 11 — Close (~30s)

> Last thing: this was built AI-natively. A Claude agent executed the planning
> docs in the /playbook folder end-to-end, with every deviation from the plan
> logged, and human review on top. The playbook ships in the repo on purpose —
> the process is part of the engineering.
>
> If you want to try it: `MOCK_LLM=1 docker compose up`, then ask it the three
> spec queries. Thanks for watching.
