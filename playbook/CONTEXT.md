# CONTEXT.md — PartSelect Chat Agent Case Study

> Read this file completely before doing anything. Every other document in this
> playbook assumes you have absorbed this context. Do not skip it.

## 1. What this project is

This is an interview case study submission for **Instalily AI**. The candidate must
design and build a chat agent for the **PartSelect** e-commerce website
(https://www.partselect.com), scoped to **Refrigerator and Dishwasher parts only**.

The deliverables are:
1. Source code (forked from https://github.com/Instalily/case-study)
2. A Loom video walkthrough (recorded by the candidate, not you — but you produce
   the demo script and talking points)
3. Optional but planned: a short slide deck

## 2. The original specification (verbatim)

> **Background** — This case study aims to design and develop a chat agent for the
> PartSelect e-commerce website. Given the extensive product catalog, the focus will
> be on Refrigerator and Dishwasher parts. The agent's primary function is to provide
> product information and assist with customer transactions. It is crucial that the
> chat agent remains focused on this specific use case, avoiding responses to
> questions outside this scope. Focus on the user experience and the extensibility
> of your implementation.
>
> **Frontend** — Use a modern framework (e.g., NextJS) for the chat interface,
> ensuring it aligns with PartSelect's branding. You will also select the features
> that you want available on the chat agent (think broadly – what do users want to
> use the chat for, how should users see products in the chat, order support, etc.).
>
> **Backend** — Choose any backend architecture that you would like. You are free to
> use any online tools, vector databases, and supplementary materials in your approach.
>
> **Success Criteria** — Your case study will be evaluated based on but not limited
> to the design of your interface, agentic architecture, extensibility and
> scalability of your approach, and ability to answer user queries accurately and
> efficiently.
>
> Example inquiries (the solution must NOT be confined to these):
> 1. "How can I install part number PS11752778?"
> 2. "Is this part compatible with my WDT780SAEM1 model?"
> 3. "The ice maker on my Whirlpool fridge is not working. How can I fix it?"

## 3. Strategy — how this submission wins

Most candidates submit: a branded chat UI + an LLM with a few tools + mock or
lightly scraped data + basic scope guarding. That is the baseline. This submission
beats it on three pillars, in priority order:

1. **A measured agent.** An eval harness with ~40 test cases and published
   accuracy numbers in the README (tool-selection accuracy, scope adherence,
   zero hallucinated part numbers). Almost no candidate proves their agent works.
2. **Hybrid retrieval done correctly.** Deterministic SQL for facts that must never
   be wrong (prices, compatibility, stock) + RAG (vector search) for fuzzy natural
   language (symptoms, descriptions). Compatibility is a database join, NEVER an
   LLM guess. This distinction must be visible in the architecture and articulated
   in the README.
3. **A complete "fix-it journey" UX.** symptom → diagnosis → recommended part →
   compatibility confirmation against the user's model → installation guide →
   add to cart. One continuous, demoable flow with rich UI components.

Secondary differentiators: real scraped PartSelect data (not mocks), streaming
responses with tool-status indicators, and a documented "built AI-natively"
meta-story (this playbook itself is part of that story — keep it in the repo
under `/playbook`).

## 4. Hard requirements (non-negotiable)

- The three example inquiries above must work flawlessly end-to-end. They will be
  the first things the evaluator types.
- The agent must politely refuse anything outside refrigerator/dishwasher parts
  (other appliances, general chit-chat, world knowledge, code, politics).
  Deflection must be graceful and on-brand, never robotic.
- The agent must never state a part number, price, stock status, or compatibility
  verdict that did not come from a tool result. System prompts and the eval
  harness both enforce this.
- The repo must run from a fresh clone in under 5 minutes following only the
  README (one command for backend, one for frontend, plus `.env` setup).
- No real API keys, scraped bulk data dumps that violate ToS, or secrets
  committed to git.

## 5. Tech stack (decided — do not relitigate)

| Layer | Choice | Why |
|---|---|---|
| Scraper | Python 3.11, `requests` + `BeautifulSoup4` + `lxml` | Pages are server-rendered; no Playwright needed |
| Database (facts + vectors) | PostgreSQL 16 + pgvector (Docker, `pgvector/pgvector:pg16`), keyword search via tsvector | One engine for relational facts AND embeddings; vector hits JOIN prices/stock in-database; production-realistic; see TRADEOFFS.md D1 |
| DB access | psycopg3, raw parameterized SQL (no ORM) | ~10 queries; the SQL is the architecture demo; see TRADEOFFS.md D2 |
| Embeddings | OpenAI `text-embedding-3-small` (env-configurable) | Cheap, good quality |
| LLM | Any OpenAI-compatible chat-completions API with tool calling. Configured via `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` env vars | Provider-agnostic = extensibility talking point; works with OpenAI, DeepSeek, etc. |
| Backend | FastAPI + uvicorn, SSE streaming | Async, typed, minimal |
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind CSS | Spec suggests NextJS |
| Eval | Plain Python script + JSON test cases, outputs a markdown table | No framework bloat |

If the forked template repo already contains a React (CRA) scaffold, adapt to it
rather than fighting it — check the template first (see 00_START_HERE.md, Phase 0).
The architecture is identical either way; only the frontend scaffold differs.

## 6. PartSelect branding (extracted from real site CSS)

- Primary teal: `#337778` (buttons use class `btn--teal` on the real site)
- Accent yellow: `#f3c04c`
- Alert/sale red: `#f4364c`
- Rating amber: `#FFC107`
- Background off-white: `#f6f6f4`
- Dark text: `#121212`, secondary text `#555453` / `#696969`, borders `#d7d7d7`
- Tone: utilitarian, trustworthy, DIY-helper. Clean cards, generous whitespace,
  no flashiness.

## 7. Repository layout (target)

```
case-study/                      # the fork
├── README.md                    # demo gif, CI badge, architecture, eval table, setup
├── Makefile                     # setup / dev / test / e2e / eval / lint / up / down
├── docker-compose.yml           # one-command bring-up (+ docker-compose.ci.yml)
├── .github/workflows/ci.yml    # lint + tests + e2e (+ manual eval job)
├── .pre-commit-config.yaml
├── playbook/                    # THIS folder — the AI-native build story
├── scraper/
│   ├── scrape.py                # CLI entry: crawl → data/raw_html cache → JSON
│   ├── parse.py                 # HTML → structured dicts (selectors in 01)
│   ├── seeds.py                 # seed URLs and crawl scope
│   └── fixtures/                # user's saved HTML pages = parser test fixtures
├── backend/
│   ├── Dockerfile               # multi-stage, non-root, healthcheck
│   ├── app/
│   │   ├── main.py              # FastAPI app, /chat SSE endpoint
│   │   ├── config.py            # pydantic-settings: ALL env config + logging setup
│   │   ├── agent.py             # agent loop (LLM + tool dispatch)
│   │   ├── llm_client.py        # OpenAI-compatible client + MOCK_LLM scripted client
│   │   ├── tools.py             # the 6 tools, typed schemas
│   │   ├── retrieval.py         # raw SQL queries + pgvector search
│   │   ├── guard.py             # scope classifier / deflection
│   │   └── prompts.py           # system prompts (single source of truth)
│   ├── data/                    # *.json datasets + seed.sql.gz (gitignore raw_html)
│   ├── tests/                   # unit + integration (pytest)
│   ├── ingest.py                # JSON → Postgres + embeddings (or --load-seed)
│   └── requirements.txt
├── eval/
│   ├── cases.json               # ~40 test cases
│   ├── run_eval.py              # runner, writes eval/RESULTS.md
│   └── RESULTS.md               # generated — committed
├── e2e/                         # Playwright happy-path journey test
└── frontend/                    # Next.js app (or adapted template) + Dockerfile
```

## 8. Working conventions for you (Claude Code)

- Work through the numbered documents in order; 00_START_HERE.md is the map.
- After every phase, run that phase's **acceptance checks** before moving on.
  Each numbered doc ends with them.
- Commit at the end of each phase with a conventional message
  (`feat(scraper): ...`, `feat(agent): ...`).
- When a doc says VERIFY, actually execute the command and read the output.
- Prefer boring, readable code over clever code. Type hints everywhere in Python,
  strict TypeScript in the frontend.
- Maintain `playbook/TRADEOFFS.md` (the decision log): when you make or
  change a significant technical decision, add/update its entry immediately —
  decision, alternatives, why, what was given up, when to revisit.
- If something in these docs conflicts with reality (e.g., the live site changed,
  the template repo differs), reality wins — adapt, leave a `NOTE:` comment in the
  code, and record the deviation in `playbook/DEVIATIONS.md` (create it on first use).
- Scraping etiquette is mandatory: 1 request per 2–3 seconds, identify with a
  normal browser User-Agent, cache every fetched page to disk, never re-fetch a
  cached URL, hard cap of ~600 pages total. If the site blocks requests, fall back
  to the user's saved HTML pages in `scraper/fixtures/` and a hand-curated dataset
  — the architecture is the deliverable, not the crawl.
