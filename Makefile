.PHONY: setup ingest dev test eval lint up down fresh smoke

PY := .venv/bin/python
PIP := .venv/bin/pip

setup:            ## venv + backend deps + frontend deps + git hooks
	python3 -m venv .venv
	$(PIP) install -r backend/requirements.txt -r backend/requirements-dev.txt ruff pre-commit
	cd frontend && npm install --no-audit --no-fund
	.venv/bin/pre-commit install

ingest:           ## load the committed seed into Postgres (no API keys needed)
	$(PY) backend/ingest.py --load-seed

rebuild-data:     ## re-ingest from JSON + re-embed via API (needs embedding key)
	$(PY) backend/ingest.py --rebuild && $(PY) backend/ingest.py --dump-seed

dev:              ## backend (:8000) + frontend (:3000) dev servers
	($(PY) -m uvicorn backend.app.main:app --reload --port 8000 &) && cd frontend && npm start

test:             ## unit + integration tests (backend & frontend)
	$(PY) -m pytest -q
	cd frontend && CI=true npx react-scripts test --watchAll=false

eval:             ## eval harness against a running backend (:8000)
	$(PY) eval/run_eval.py

smoke:            ## the three canonical spec queries against :8000
	bash backend/smoke.sh

lint:             ## ruff + format check
	.venv/bin/ruff check backend scraper eval tests
	.venv/bin/ruff format --check backend scraper eval tests

up:               ## docker compose up (set MOCK_LLM=1 for keyless demo)
	docker compose up --build -d

down:
	docker compose down

fresh:            ## clean-clone simulation: build everything and smoke it
	docker compose down -v --remove-orphans || true
	MOCK_LLM=1 MOCK_EMBEDDINGS=1 docker compose up --build -d
	sleep 5 && BASE=http://localhost:8000 bash backend/smoke.sh

help:
	@grep -E '^[a-z-]+:.*##' Makefile | sed 's/:.*##/ —/'
