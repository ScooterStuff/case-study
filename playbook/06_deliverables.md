# 06_deliverables.md — README, Documentation & Final Polish

## Objective
Package the repo for evaluation. The evaluator's path is: README → run it →
type the three spec queries → skim code. Optimize that path. (The candidate
handles video/presentation separately — out of scope for you; just leave
`playbook/TALKING_POINTS.md` tidy as raw material.)

## 1. README.md (rewrite the fork's README)

Order matters — structure:
1. **Hero**: one-line pitch ("A grounded PartSelect chat agent that takes a
   customer from symptom to verified, in-cart part — with measured accuracy")
   + demo GIF of the fix-it journey (15–20s, looped, ≤ 8MB, stored in
   `docs/media/`) + CI badge (Phase 7).
2. **Quickstart** (must work verbatim — two paths):
   ```
   # Docker (zero local toolchain)
   cp .env.example .env   # add LLM key, or set MOCK_LLM=1
   docker compose up --build

   # Local dev
   cp .env.example .env && make setup && make dev
   ```
   Note: datasets + seed.sql.gz are pre-committed — no scraping or embedding
   key needed to run (`ingest.py --load-seed` runs automatically).
3. **Eval results** — embed the summary table from eval/RESULTS.md + the line
   "0 hallucinated part numbers across N cases; 100% scope adherence". Link to
   methodology in eval/.
4. **Architecture** — embed the flowchart AND the narration paragraph from
   `playbook/ARCHITECTURE.md` verbatim (GitHub renders Mermaid). Include the
   sequence diagram in a collapsible `<details>` block.
5. **Features** — list with small screenshots of each rich block
   (`docs/media/`).
6. **Testing & quality** — testing pyramid summary (Phase 7), how to run each
   layer, coverage number, link to CI runs.
7. **Design decisions & trade-offs** — a short table of the 5 biggest
   decisions (one line each: decision → why → revisit-when), linking to
   `playbook/TRADEOFFS.md` for the full ADR-style log. This section exists so
   interviewers can see trade-off thinking without asking.
8. **Extensibility** — concretely: add an appliance = new seed URLs + enum
   value; real order support = replace `order_support` tool body with OMS/ERP
   client (schema already the contract); swap LLM provider = 3 env vars; scale
   path = Postgres+pgvector, Redis sessions, per-tool caching, OTel on the
   existing structured logs.
9. **Limitations (honesty section)** — partial cross-reference data
   (pagination), mocked orders, single-locale pricing, in-memory sessions,
   small catalog slice. Honesty here reads as seniority.
10. **How this was built (AI-native note)** — built with Claude Code driven by
   the planning docs in `/playbook`; human-reviewed. Humble and factual.
11. **Dev guide** — pre-commit setup, Makefile targets, /docs OpenAPI link,
    CONTRIBUTING.md link.

## 2. Final polish checklist
- [ ] Fresh-clone test in /tmp following README only — BOTH quickstart paths
      work; three spec queries pass in the UI
- [ ] `make lint` and `make test` green; CI green on the fork
- [ ] `grep -rI "sk-" --exclude-dir=node_modules .` → no keys; .env untracked
- [ ] Remove dead code; TODOs resolved or moved to README limitations
- [ ] Screenshots + GIF committed under `docs/media/`
- [ ] eval/RESULTS.md regenerated on final code (git sha matches HEAD)
- [ ] playbook/DEVIATIONS.md and TALKING_POINTS.md tidy — part of the story
- [ ] ARCHITECTURE.md diagram matches the code as actually built
- [ ] TRADEOFFS.md reviewed end-to-end: every entry reflects what was ACTUALLY
      built; stale entries updated; the rehearsal one-liners still true
- [ ] Final commit + tag `v1.0`; verify the fork pushes cleanly
