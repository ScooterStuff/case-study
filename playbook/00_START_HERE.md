# 00_START_HERE.md — Build Orchestration

You are Claude Code, building the PartSelect chat agent case study end-to-end.
**Read `CONTEXT.md` first.** It contains the spec, strategy, stack decisions,
branding, repo layout, and your working conventions. Nothing below makes sense
without it.

## Document map

| Order | Doc | Produces | Depends on |
|---|---|---|---|
| — | `CONTEXT.md` | shared context | — |
| 0 | this file, Phase 0 below | repo skeleton, env check | — |
| 1 | `01_data_scraping.md` | `scraper/`, JSON datasets | Phase 0 |
| 2 | `02_data_layer.md` | Postgres+pgvector schema, `ingest.py`, seed dump | 1 |
| 3 | `03_backend_agent.md` | FastAPI app, agent, tools, guard | 2 |
| 4 | `04_frontend.md` | Next.js chat UI, rich components | 3 (API contract) |
| 5 | `05_eval_harness.md` | `eval/`, RESULTS.md with numbers | 3 |
| 6 | `07_testing_ci.md` | consolidated test pyramid, CI pipeline | 3, 4 |
| 7 | `08_docker_devops.md` | Docker, Makefile, config/logging hygiene | 3, 4 |
| 8 | `06_deliverables.md` | README, docs, final polish | all |
| — | `ARCHITECTURE.md` | canonical Mermaid diagrams (embed in README) | reference |

Execution order: 0 → 1 → 2 → 3 → 5 → 4 → 7(testing) → 8(docker) → 6(polish).
Phase 5 (eval) before Phase 4 (frontend) — a measured backend makes frontend
debugging easier; they may run in parallel if you can. Testing and Docker come
after features exist; deliverables/polish is always last. Note tests required
by earlier phases (parser tests in 1, retrieval tests in 2, agent tests in 3)
are written IN those phases — 07 consolidates and fills gaps, it doesn't defer
all testing to the end.

## Phase 0 — Repo skeleton and environment (do now)

1. Confirm the working directory is the candidate's fork of
   `Instalily/case-study`. Inspect whatever template code exists before writing
   anything. Record in `playbook/DEVIATIONS.md`:
   - Is there an existing frontend scaffold? (Historically the template is a
     Create-React-App chat skeleton with an `api/api.js` calling a `getAIMessage`
     function.) If CRA exists, **adapt it** instead of introducing Next.js, and
     apply 04_frontend.md's component specs to CRA — the doc tells you how.
   - Any provided README instructions? Follow them where they don't conflict.
2. Create the directory layout from CONTEXT.md §7 (empty `__init__.py` /
   placeholder files are fine).
3. Create `backend/requirements.txt`:
   `fastapi`, `uvicorn[standard]`, `httpx`, `beautifulsoup4`, `lxml`,
   `psycopg[binary]`, `pgvector`, `openai` (used as a generic OpenAI-compatible client),
   `pydantic>=2`, `python-dotenv`, `sse-starlette`.
4. Create `.env.example` (never `.env`) with:
   ```
   LLM_BASE_URL=https://api.openai.com/v1
   LLM_API_KEY=sk-...
   LLM_MODEL=gpt-4o
   DATABASE_URL=postgresql://ps:ps@localhost:5432/partselect
   EMBEDDING_MODEL=text-embedding-3-small
   EMBEDDING_API_KEY=            # defaults to LLM_API_KEY if empty
   ```
5. Create root `.gitignore`: `node_modules/`, `.env`, `__pycache__/`,
   `scraper/data/raw_html/`, `.next/`.
   Note: the JSON datasets and `backend/data/seed.sql.gz` ARE committed —
   the evaluator must be able to run without scraping or embedding keys.
6. `git commit -m "chore: scaffold repo structure and environment"`

**Acceptance checks (Phase 0):**
- [ ] `python3 -c "import fastapi, psycopg, pgvector, bs4"` succeeds in a venv
- [ ] Tree matches CONTEXT.md §7 (allowing for template adaptations)
- [ ] `playbook/DEVIATIONS.md` exists and records the template findings

## Standing orders (apply to every phase)

- End every phase by running its acceptance checks and committing.
- The three canonical queries from the spec are your smoke test from Phase 3
  onward. Keep them in a script: `backend/smoke.sh`.
- Never let the agent invent part data. If you ever observe a hallucinated PS
  number during development, treat it as a P0 bug: fix the prompt/tool, then add
  a regression case to `eval/cases.json`.
- Keep a running list of "talking points discovered while building" in
  `playbook/TALKING_POINTS.md` — anything surprising, any tradeoff made. These
  feed the Loom script in Phase 6.

## Definition of done (whole project)

- [ ] All phase acceptance checks pass
- [ ] `eval/RESULTS.md` shows: 100% scope adherence, 0 hallucinated part numbers,
      ≥90% correct tool selection, and per-case latency
- [ ] The three spec queries produce correct, rich-component answers in the UI
- [ ] `pytest` + `vitest` + Playwright e2e green; backend coverage ≥80%; CI green
- [ ] `docker compose up --build` brings up the whole app (incl. MOCK_LLM=1 mode)
- [ ] Fresh-clone test: `git clone` to a temp dir, follow README only, app runs
- [ ] README contains: hero demo GIF, CI badge, Mermaid architecture diagram
      (from ARCHITECTURE.md), eval table, testing section, extensibility
      section, limitations section, AI-native build note
