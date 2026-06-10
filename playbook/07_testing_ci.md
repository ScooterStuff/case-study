# 07_testing_ci.md — Testing Strategy & Continuous Integration

## Objective
A proper testing pyramid plus a GitHub Actions pipeline that runs on every push.
Phases 1–5 already created scattered tests; this phase consolidates them into a
coherent, documented strategy and adds the missing layers. A green CI badge in
the README is part of the deliverable.

## Testing pyramid

```
        e2e (few)          eval harness + one Playwright happy-path
      integration (some)   API-level tests, real DB, mocked LLM
    unit (many)            parsers, retrieval, guard, validators, components
```

The eval harness (Phase 5) is the top of the pyramid for *agent quality*;
this phase covers *software correctness*. Keep them distinct — say so in the
README: "evals measure whether the agent is right; tests measure whether the
code is correct."

## Backend tests (`backend/tests/` + `scraper/tests/`, pytest)

Unit (no network, no LLM, milliseconds):
1. `test_parse.py` — (exists from Phase 1) parsers vs saved fixtures.
2. `test_retrieval.py` — (exists from Phase 2) against a dedicated test
   database: `conftest.py` creates schema in a `partselect_test` db on the same
   Postgres container and loads `tests/fixtures/mini_parts.json` (10 parts,
   with tiny precomputed fixture embeddings — no API calls) — NOT the prod
   data, so tests are fast and deterministic. Truncate between tests.
3. `test_guard.py` — fast-path allowlist hits/misses; classifier called only
   when expected (mock the LLM client, assert call counts).
4. `test_validator.py` — hallucination validator: known PS passes, unknown PS
   raises, PS numbers inside tool results are allowed, regex edge cases
   (PS embedded in words, lowercase ps, punctuation).
5. `test_tools.py` — each tool against the test db: happy path + not-found +
   malformed input (Pydantic validation errors returned as tool errors, not
   crashes).
6. `test_agent_loop.py` — mock LLM returning scripted tool_calls; assert: loop
   terminates at max iterations, parallel tool execution, tool errors surfaced
   gracefully, history compaction works, SSE event ordering
   (tool_start → tool_end → tokens → done).

Integration (`test_api.py`, FastAPI TestClient, mocked LLM):
- `POST /chat` streams valid SSE; malformed body → 422; unknown session
  creates one; `/health` reports counts; CORS headers present.

Conventions: `pytest -q` from repo root via `pyproject.toml` config; target
≥80% coverage on `backend/app/` (`pytest --cov`, enforce with
`--cov-fail-under=80` in CI); no test may hit the network (enforce with
`pytest-socket`).

## Frontend tests (`frontend/`, Vitest + React Testing Library)

1. `blocks/*.test.tsx` — each rich block renders from a fixture payload
   (ProductCard shows price/stock; CompatResult shows correct icon per verdict
   incl. the honesty note for `no_match_found`; Diagnosis renders ranked causes).
2. `lib/sse.test.ts` — SSE parser: chunked event reassembly, interleaved
   event types, malformed event tolerance, abort handling.
3. `Composer.test.tsx` — Enter sends, Shift+Enter newline, disabled while
   streaming.
Snapshot tests only for the empty state; behavior assertions everywhere else.

## E2E (one test, Playwright, `e2e/journey.spec.ts`)
Boot both servers (or docker compose — Phase 8), run the fix-it journey:
type ice-maker symptom → diagnosis block appears → click a part →
"Check fits my model" → type model → verdict block → add to cart → cart badge
increments. Runs headless in CI against the mocked-LLM backend mode (add env
`MOCK_LLM=1` to the backend: a deterministic scripted client used by tests —
implement it in `backend/app/llm_client.py` as a drop-in).

## Static quality gates
- Python: `ruff check` + `ruff format --check` + `mypy backend/app --strict`
  (pragmatic: allow `--ignore-missing-imports`).
- TypeScript: `tsc --noEmit`, `eslint`, `prettier --check`.
- `pre-commit` config running ruff/prettier/eslint + `detect-secrets` hook;
  document `pre-commit install` in README dev section.

## CI (`.github/workflows/ci.yml`)
Jobs (run in parallel where possible):
1. `backend`: setup Python 3.11 → cache pip → `services: postgres`
   (pgvector/pgvector:pg16 service container, health-checked) → ruff + mypy →
   pytest w/ coverage → upload coverage artifact.
2. `frontend`: setup Node 20 → cache npm → lint + tsc → vitest → `next build`
   (or CRA build).
3. `e2e`: needs backend+frontend → docker compose up (MOCK_LLM=1) → playwright.
4. `eval` (manual trigger only, `workflow_dispatch`, needs real LLM secret):
   runs `eval/run_eval.py`, uploads RESULTS.md artifact. Do NOT run on every
   push (cost); say so in a comment.
Badge in README. No secrets in logs; LLM key only in the manual eval job via
GitHub secrets.

## Acceptance checks
- [ ] `pytest -q` green locally, coverage ≥80% on backend/app
- [ ] `npm test` green; `npx playwright test` green with MOCK_LLM=1
- [ ] `pre-commit run --all-files` clean
- [ ] CI green on GitHub for all push-triggered jobs (verify on the fork)
- [ ] README dev section documents: run tests, run e2e, pre-commit setup
- [ ] `git commit -m "test: testing pyramid + CI pipeline"`
