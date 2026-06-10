# DEVIATIONS.md — where reality differed from the playbook

## Phase 0 — template findings

1. **Template is the predicted CRA chat skeleton.** `Instalily/case-study` (2 commits)
   is a Create-React-App scaffold: `src/components/ChatWindow.js` renders markdown via
   `marked` + `dangerouslySetInnerHTML`, and `src/api/api.js` exposes a stub
   `getAIMessage(userQuery)`. Per CONTEXT.md §5 we **adapt CRA** instead of introducing
   Next.js; 04_frontend.md component specs will be applied to CRA.
2. **Template moved to `frontend/`.** The CRA app lived at the repo root; CONTEXT.md §7
   requires a `frontend/` subdir alongside `backend/`, `scraper/`, etc. Moved with
   `git mv` (history preserved). CRA boilerplate README moved to `frontend/README.md`;
   root README is rewritten in Phase 6.
3. **Template package.json is messy** (name `chrome-side-panel`; unused heavy deps:
   `langchain`, `antd`, `rsuite`, `@anthropic-ai/sdk`, `pdf-parse`, `fs`, `chrome`,
   `mui`...). Will prune to what we use in Phase 4 and rename the package.
4. **No usable template README instructions** — only CRA boilerplate. Nothing to follow.

## Phase 0 — environment findings

5. **Python 3.10 in the build sandbox** (playbook assumes 3.11). Code is written
   3.10-compatible; Docker images pin 3.11 so the shipped artifact matches the playbook.
6. **No Docker in the build sandbox.** Dockerfiles/compose are authored per
   08_docker_devops.md but `docker compose up` cannot be executed here; acceptance
   checks that need a live container use the documented fallbacks (syntax validation +
   running services directly). Final verification of compose is on the candidate's machine.
7. **No PostgreSQL preinstalled in the sandbox.** Phase 2 will attempt an apt install of
   Postgres + pgvector inside the sandbox; if that fails, retrieval tests run against
   the documented fallback and the seed dump is still produced for the evaluator.
8. **Git cannot operate directly on the synced workspace folder** (its lock-file
   rename pattern corrupts files on the sync layer). The canonical repo lives in the
   sandbox filesystem; the full tree **including `.git`** is mirrored back to the
   workspace folder at the end of every phase. `scraper/fixtures/` flows the other
   way (user drops saved HTML there; pulled into the repo before parsing).
9. **Fork `ScooterStuff/case-study` not reachable yet** (clone 404s). Built on a full
   clone of `Instalily/case-study` with the remote named `upstream`; history is intact
   so the work can be pushed to the fork once it exists / credentials are provided.

## Phase 1 — scraping

10. **PS11752778 is NOT a dishwasher door balance link kit.** The playbook said to
    verify it as one; the live site says it is a **Whirlpool Refrigerator Door Shelf
    Bin (WPW10321304)**, $47.40, In Stock. Reality wins: the dataset stores the truth.
    Consequence: spec query 2 ("Is this part compatible with my WDT780SAEM1 model?")
    correctly answers *not a verified fit* when "this part" = PS11752778 (a fridge
    bin vs. a dishwasher model) — the agent explains this gracefully and offers the
    12 parts that ARE verified for WDT780SAEM1. The 01 acceptance item
    "compatibility.json includes (PS11752778, WDT780SAEM1)" is therefore
    intentionally unmet; the model's own parts list was harvested instead.
11. **No raw-HTML access from the build environment.** Only text *extractions* of
    live pages were retrievable (and no browser was connected), so:
    - `scraper/parse.py` (raw-HTML parsers per the playbook selectors) is written
      but its fixture tests stay **skipped until the candidate drops saved HTML
      pages into `scraper/fixtures/`**.
    - The committed datasets were built from live-page text extractions via
      `scraper/extract_text.py` (real data, every record carries `source_url` +
      `scraped_at`). One extraction is committed as a test fixture.
12. **Dataset volume below the 150-part target: 34 parts** (19 dishwasher / 15
    refrigerator, incl. all spec-critical records), 1,136 compatibility rows
    (≥1,000 ✓), 21 repair guides (≥16 ✓). The playbook's documented fallback
    applies ("the architecture, not crawl volume, is evaluated"); running
    `python -m scraper.scrape` on a normal machine scales the same pipeline to the
    full target without code changes.
13. **Repair guides are two-tier**: 2 `detail_level: "full"` guides with ranked
    causes + inspection steps (refrigerator Not-Making-Ice, dishwasher
    Not-Draining — the two the spec queries need), 19 `detail_level: "summary"`
    guides from the official symptom-index blurbs (title, % reported, summary,
    source URL). scrape.py upgrades summaries to full when run with HTML access.

## Phase 2 — data layer

14. **No Docker in the build sandbox → `pgserver` (pip) for local Postgres.** All
    retrieval tests run against an embedded Postgres 16.2 with pgvector 0.6.2 —
    a *real* Postgres, not a fake. `docker-compose.yml` (db service per the
    playbook) is authored and is the evaluator path; `docker compose up -d db`
    itself must be smoke-tested on the candidate's machine.
15. **Committed `seed.sql.gz` currently contains MOCK embeddings** (no embedding
    API key available yet). The restore path is fully verified keyless (34 parts /
    1,130 compat rows / 358 embeddings). When the key lands: re-run
    `python backend/ingest.py --rebuild && python backend/ingest.py --dump-seed`
    to swap in real vectors (est. cost < $0.01).
16. **02 acceptance deltas, all traced to earlier deviations:** parts count is 34
    not ≥150 (#12); `get_part('PS11752778')` returns the *door shelf bin* not a
    "door balance link kit" (#10); `check_compat('PS11752778','WDT780SAEM1')`
    correctly returns `no_match_found` with evidence, not `verified_fit` (#10) —
    `check_compat('PS3406971','WDT780SAEM1')` covers the `verified_fit` path.
    `pg_dump` is taken with `--inserts` so `--load-seed` works through psycopg
    with no psql dependency.

## Phase 3 — agent

17. **Smoke + agent tests run in MOCK_LLM mode** (no API key yet). The mock is a
    deterministic router that obeys the same tool contracts and grounding rules;
    the SSE protocol, guard, tools, and hallucination gate are fully exercised.
    Re-run `backend/smoke.sh` + the eval with the real LLM once the key lands.
18. **Background processes do not survive between build-sandbox commands** (each
    command runs in an isolated bwrap), so server-dependent checks run as
    single-shot scripts that bring up Postgres + uvicorn, test, and tear down.
    No impact on the shipped repo.

## Phase 5 — eval

19. **Published RESULTS.md is from a MOCK_LLM run** (no key yet): 40/40, 0
    hallucinated part numbers, 100% tool selection & scope adherence, p50 31ms.
    The mock proves the rails (guard, tools, grounding, SSE protocol, validator);
    it does NOT prove the language model. When the key lands: start the backend
    without MOCK_LLM and re-run `python eval/run_eval.py` to regenerate
    RESULTS.md with the real model before submitting. RESULTS.md states the
    model name in its metadata line, so the provenance is always explicit.
