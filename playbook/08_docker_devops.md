# 08_docker_devops.md — Docker, Dev Experience & Operational Hygiene

## Objective
One-command bring-up (`docker compose up`), plus the operational practices that
make the repo read as production-minded: structured config, logging, error
handling, request tracing, and a Makefile. "Extensibility and scalability" is a
stated grading criterion — this phase is its proof.

## Docker

`backend/Dockerfile` (multi-stage):
- Stage 1 `builder`: `python:3.11-slim`, install requirements into a venv.
- Stage 2 `runtime`: slim base, copy venv, copy app + `data/` (json datasets
  and seed.sql.gz baked in; entrypoint runs `ingest.py --load-seed` against db
  if tables are missing — self-healing first boot, no scraping at runtime),
  non-root `appuser`, `EXPOSE 8000`,
  `HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1`,
  `CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]`.

`frontend/Dockerfile` (multi-stage):
- `node:20-alpine` deps → build → run stage. For Next.js use
  `output: 'standalone'` in next.config for a small runtime image; for a CRA
  template, build then serve via `nginx:alpine` with a 10-line nginx.conf that
  proxies `/api/*` → `backend:8000` (avoids CORS entirely in container mode).

`docker-compose.yml` (repo root):
```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment: [POSTGRES_USER=ps, POSTGRES_PASSWORD=ps, POSTGRES_DB=partselect]
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck: {test: ["CMD-SHELL","pg_isready -U ps -d partselect"], interval: 5s, retries: 10}
  backend:
    build: ./backend
    env_file: .env            # LLM_* vars; MOCK_LLM=1 works for keyless demo
    environment: [DATABASE_URL=postgresql://ps:ps@db:5432/partselect]
    depends_on:
      db: {condition: service_healthy}
    ports: ["8000:8000"]
    healthcheck: {test: ["CMD","curl","-f","http://localhost:8000/health"], interval: 10s, retries: 5}
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on:
      backend: {condition: service_healthy}
      environment: [NEXT_PUBLIC_API_URL=http://localhost:8000]
volumes: {pgdata: {}}
```
(The db service was introduced minimally in Phase 2 — this phase finalizes it.)
Also `docker-compose.ci.yml` overlay setting `MOCK_LLM=1` for the e2e job
(Phase 7). `.dockerignore` in both contexts (node_modules, .next, __pycache__,
raw_html, .env, .git).

Verify image sizes are sane (backend < ~400MB, frontend
< ~200MB); note them in DEVIATIONS.md if wildly off.

## Makefile (repo root — the developer UX front door)
```
make setup      # venv + pip install + npm install + pre-commit install
make ingest     # ingest.py --rebuild (or --load-seed) into Postgres
make dev        # backend + frontend dev servers concurrently
make test       # pytest + vitest
make e2e        # compose up (mock) + playwright
make eval       # run eval harness against local backend
make lint       # ruff + mypy + eslint + tsc
make up / down  # docker compose
make fresh      # clean clone simulation: clean build + up + smoke.sh
```
README quickstart becomes: `cp .env.example .env && make setup && make dev`
(with `docker compose up` as the zero-Python alternative).

## Configuration management
- Single typed settings object: `backend/app/config.py` using
  `pydantic-settings` (`BaseSettings`) — all env vars declared once with types,
  defaults, and docstrings. No bare `os.getenv` anywhere else (add a ruff ban
  via comment convention or grep check in CI).
- `MOCK_LLM`, `LOG_LEVEL`, `DATABASE_URL` all flow through it.
- Frontend: only `NEXT_PUBLIC_API_URL`.

## Logging & observability (lightweight, not over-engineered)
- `structlog` (or stdlib logging with a JSON formatter) — one logger config in
  `config.py`. Human-readable in dev (`LOG_LEVEL=DEBUG`, pretty), JSON in
  container.
- Per-request `request_id` (uuid) via FastAPI middleware; included in every log
  line and returned as `X-Request-ID` header.
- Log per chat turn: session_id, guard decision, tools called + per-tool
  latency, LLM tokens (if reported), total latency, validator triggers. These
  lines ARE the observability story — mention in README that in production
  they'd ship to Datadog/OTel, and the structure is already there.
- Error handling: one exception-handler middleware → JSON `{error, request_id}`
  with correct status codes; tool failures never 500 the stream — they emit a
  `tool_error` SSE event and the agent recovers conversationally ("I had
  trouble checking that — here's what I can tell you…"). Add a test for this
  in Phase 7's `test_agent_loop.py` if not already present.

## Repo hygiene additions
- `.editorconfig` (2-space ts, 4-space py, lf, final newline).
- `LICENSE` — MIT (unless the fork's template dictates otherwise).
- `CONTRIBUTING.md` — short: setup, test, commit conventions (it signals habit
  even in a solo repo).
- Dependency pinning: `pip-compile` style pinned `requirements.txt` (or at
  minimum `~=` pins) and committed `package-lock.json`.
- API contract: FastAPI's auto `/docs` (OpenAPI) — link it in README; ensure
  Pydantic models give it accurate schemas (this doubles as API documentation
  for free).

## Acceptance checks
- [ ] `docker compose up --build` → UI on :3000 answers the three spec queries
      (with real key) AND with `MOCK_LLM=1` (scripted demo answers)
- [ ] `docker compose ps` shows backend healthy via healthcheck
- [ ] `make fresh` passes end-to-end on a clean checkout
- [ ] Logs are JSON in container, pretty in dev; X-Request-ID present
- [ ] Kill the LLM key mid-session → graceful error event, no stack trace to
      the user, request_id logged
- [ ] `git commit -m "feat(ops): docker, makefile, structured config/logging"`
