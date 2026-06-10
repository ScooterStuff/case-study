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
