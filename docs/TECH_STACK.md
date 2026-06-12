# Technology Choices

> Why each piece of the stack is here, what was considered instead, and the
> trigger that would make us revisit. Architectural decisions (one-DB-for-both,
> single-agent-with-tools, buffer-and-release validator) live in
> [`playbook/TRADEOFFS.md`](../playbook/TRADEOFFS.md); this file is about the
> _libraries and runtimes_ in `requirements.txt` and `package.json`.

## Details

### Python 3.12

- **Why.** The LLM ecosystem (OpenAI SDK, embedding clients, eval libraries)
  is Python-first; talent and examples are densest here. 3.12 specifically
  for `tomllib` in stdlib (no extra TOML dep), better error messages, and
  `Literal[tuple]` support that lets [appliances.py](../backend/app/appliances.py)
  build the tool-arg enum from TOML at import time.
- **Considered.** Node.js (would have unified the stack with the React frontend
  and given native streaming primitives), Go (best raw latency, single binary).
- **Rejected because.** Both would force a rewrite of the agent/tooling layer
  with thinner SDK ergonomics for marginal latency gains. The hot path is the
  LLM call (hundreds of ms), not the request handler (sub-ms).
- **Revisit when.** The hot path stops being the LLM (e.g. heavy local
  retrieval reranking) or we ship a multi-tenant edge-runtime variant.

### FastAPI 0.136

- **Why.** Streaming endpoints (`EventSourceResponse`), Pydantic-validated
  request bodies, free OpenAPI/Swagger UI at `/docs`, and starlette middleware
  for the request-id stamp ([backend/app/main.py](../backend/app/main.py)).
- **Considered.** Flask (would have needed Quart for async + extra deps for
  OpenAPI + manual pydantic wiring), Django (overkill — no admin, no ORM, no
  templates needed), bare Starlette (FastAPI _is_ Starlette + the bits we'd
  add by hand).
- **Rejected because.** None of the alternatives shrink the dependency list
  while keeping async streaming and typed bodies.
- **Revisit when.** We need GraphQL or a non-trivial admin UI.

### SSE over WebSockets

- **Why.** Tokens, tool-status pills, and `ui_block` events are all
  server-to-client. SSE gives that with plain HTTP, auto-reconnect, no upgrade
  handshake, and it works through every corporate proxy. Easy to curl
  ([backend/\_sse_pretty.py](../backend/_sse_pretty.py)) and easy to replay in
  the eval harness.
- **Considered.** WebSockets (overkill — we don't need bidirectional), HTTP
  long-polling (worse UX, more reconnect logic).
- **Revisit when.** The client needs to push mid-turn (e.g. cancel button
  beyond a simple `AbortController`).

### Postgres 16 + `pgvector`

- **Why.** The architecture's headline trick is "compatibility is a JOIN, not
  an LLM guess". Putting the embeddings table in the same database means a
  semantic hit can `JOIN parts ON ps_number` for price/stock in one query.
  Production-shaped from day one; one `docker compose up`.
- **Considered.** SQLite + Chroma (simpler local story but two engines to
  back up and no in-engine JOINs across them), Pinecone/Qdrant/Weaviate
  (managed scale at the cost of a network hop and a vendor), Elasticsearch
  hybrid (heavy JVM footprint for our scale).
- **Rejected because.** The split-engine path forces the JOIN into Python,
  which is exactly the layer we want to keep boring.
- **Revisit when.** Embedding count crosses ~1M (HNSW build times) or we need
  multi-tenant row-level isolation that pgvector doesn't help with.

### `psycopg` 3 (binary), no ORM

- **Why.** ~10 hand-written queries in
  [backend/app/retrieval.py](../backend/app/retrieval.py). The SQL _is_ the
  architecture demo — a JOIN for compatibility, two queries + reciprocal-rank
  fusion for hybrid search, a tsvector + cosine combo. An ORM would obscure
  exactly what we want a reviewer to read.
- **Considered.** SQLAlchemy core (still adds dialect machinery for 10
  queries), SQLModel (locks us to ORM patterns we don't need), asyncpg (would
  force async retrieval; we run tools in a thread pool anyway).
- **Revisit when.** Schema churns 3× or query count grows past ~30.

### `openai` SDK (OpenAI-compatible), no agent framework

- **Why.** Three env vars (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`) point
  the client at any compatible provider — OpenAI, Together, Fireworks, vLLM,
  Ollama with the OAI shim. The agent loop is ~150 lines of explicit code
  ([agent.py](../backend/app/agent.py)) — no framework, no hidden retries,
  no "magic" the eval harness can't see.
- **Considered.** LangChain / LlamaIndex (excellent for prototyping; come
  with churn, broad surface area, and abstractions that make the validator
  and SSE seam awkward), Anthropic SDK direct (would tie us to one vendor
  for no benefit — the OAI shape is the lingua franca).
- **Rejected because.** "Show me the loop" was a deliberate goal; a framework
  would inhibit the tool-call honesty trace and the buffer-and-release
  hallucination gate.
- **Revisit when.** The tool registry stops fitting one prompt or we add
  parallel sub-agents that need their own contexts.

### React 18 + Create React App

- **Why.** The case-study spec referenced a CRA template; keeping it cuts
  scope. SPA fits the chat surface (no SEO, no SSR needs). React 18's
  concurrent rendering keeps the streaming token UI smooth.
- **Considered.** Next.js (SSR/SSG features we don't use here; heavier
  deploy story), Vite (faster dev server but rewriting the template wasn't
  free), SvelteKit (smaller bundles; team familiarity weighed more).
- **Revisit when.** We need SEO landing pages, server components, or a
  multi-page admin app around the chat.

### Tesseract.js (client-side OCR), lazy-loaded

- **Why.** "Snap the appliance sticker" should work without sending the photo
  anywhere. Tesseract.js runs in the browser, the model number never leaves
  the device, and we lazy-load the ~2 MB worker bundle only when the user
  clicks the camera button — the initial chat bundle is unaffected.
- **Considered.** Cloud OCR (Google Vision, AWS Textract — better accuracy
  but adds a vendor, a billing line, and a privacy story we'd rather not
  have), server-side Tesseract (same dependency, worse latency, and we'd
  ship the photo over the wire).
- **Revisit when.** Accuracy on real customer stickers becomes a measured
  blocker; cloud OCR is then a 50-line server route.

### BeautifulSoup + lxml (no Scrapy, no Playwright)

- **Why.** PartSelect's pages are static HTML; no JS rendering needed.
  `httpx` for fetching with cache, BS4+lxml for parsing — a single-file
  scraper ([scraper/scrape.py](../scraper/scrape.py)) that's polite (caching
  - rate limiting) and offline-replayable from `data/raw_html/`.
- **Considered.** Scrapy (its scheduling/middleware model is overkill for
  ~150 URLs from one host), Playwright (we'd be paying for a headless
  browser to render pages that don't need it).
- **Revisit when.** A target page is JS-rendered or auth-walled.

### TOML for appliance configuration

- **Why.** Adding an appliance is a one-file edit
  ([appliances.toml](../backend/app/appliances.toml)). TOML has comments,
  no significant-whitespace foot-guns, and Python 3.12 reads it from stdlib
  (`tomllib`) with zero extra deps. The Pydantic tool enum, scope guard,
  system prompt, and MockLLM router all rebuild from this file at import
  time.
- **Considered.** JSON (no comments, one-line edits get noisy), YAML
  (whitespace bugs, extra dep), hardcoded Python tuples (the original
  state — the very thing this file replaced).
- **Revisit when.** We need nested or per-tenant config that outgrows a flat
  TOML; small JSON-Schema or Pydantic-validated YAML would be next.

### pytest + Ruff

- **Why.** pytest is the de-facto standard; ruff replaces flake8 + black +
  isort + bandit with one ~10 MB binary that runs ~100× faster on the
  pre-commit hook. CI runs `ruff check`, `ruff format --check`, and pytest
  with coverage in seconds.
- **Considered.** unittest (less ergonomic fixtures), the multi-tool linter
  stack (slower, four configs to maintain).
- **Revisit when.** Ruff lacks a rule we need (so far it has every bandit
  rule we care about via its `S` selector).

### Docker Compose (not Kubernetes)

- **Why.** Single-node demo. Reviewer types `docker compose up --build` and
  has the full stack — Postgres+pgvector, FastAPI, React — on three ports.
- **Considered.** k8s / kind / Nomad (overkill for a one-machine deploy),
  bare-metal (forces the reviewer to install Postgres + pgvector locally).
- **Revisit when.** This actually ships somewhere with HA or autoscaling
  needs; the same images move straight to ECS/Fly/Render/etc.

### `pgserver` (embedded Postgres for tests)

- **Why.** Tests run real Postgres+pgvector with no Docker daemon required —
  a key constraint when the build environment didn't have Docker. CI uses
  the real container; local dev gets feature-parity for free.
- **Considered.** testcontainers (needs Docker), mocked DB (can't validate
  pgvector cosine math or hybrid search RRF), SQLite (no pgvector parity).
- **Revisit when.** `pgserver` lags Postgres versions we need.

## What's deliberately _not_ in the stack

- **No Redis.** Sessions are in-memory dicts because a single process is the
  demo target. Swapping in Redis is a one-class change (noted in the README's
  Limitations).
- **No Celery / queue.** No background work that warrants it; ingestion is a
  one-shot CLI.
- **No Sentry / OTel SDK in the box.** Structured logs with a per-request ID
  are emitted; shipping them is a deploy-time decision.
- **No CDN/edge worker for the frontend.** CRA `build/` is served by nginx
  in the Docker image — perfectly fine until traffic exists.

## How to revisit a choice

Each row above has a "revisit when" — those are the only triggers that
should reopen the discussion. Anything else is bikeshedding. New decisions
that change the architecture (not just the library) get a new entry in
[`playbook/TRADEOFFS.md`](../playbook/TRADEOFFS.md); new library swaps get
a row added here.
