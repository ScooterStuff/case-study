# Eval Results

- **Model:** MOCK  |  **Date:** 2026-06-10 22:53 UTC  |  **Git:** `4bdf354`
- **Methodology:** every case replays its turns through the live SSE `/chat` API in a fresh session; a failing case is retried once (LLM nondeterminism) before being marked failed.

## Summary

| Metric | Value |
|---|---|
| Overall pass rate | **40/40 (100%)** |
| Tool-selection accuracy | 100% |
| Scope adherence | 100% |
| Hallucinated part numbers | **0** |
| Latency p50 / p95 | 40 ms / 126 ms |

| Suite | Passed |
|---|---|
| compatibility | 8/8 |
| diagnosis | 6/6 |
| grounding | 5/5 |
| injection | 4/4 |
| scope | 8/8 |
| search_fuzzy | 6/6 |
| spec_canonical | 3/3 |

## Per-case results

| Case | Suite | Result | Latency | Note |
|---|---|---|---|---|
| compat_01 | compatibility | ✅ | 88 ms |  |
| compat_02 | compatibility | ✅ | 62 ms |  |
| compat_03 | compatibility | ✅ | 24 ms |  |
| compat_04 | compatibility | ✅ | 34 ms |  |
| compat_05 | compatibility | ✅ | 31 ms |  |
| compat_06 | compatibility | ✅ | 92 ms |  |
| compat_07 | compatibility | ✅ | 38 ms |  |
| compat_08 | compatibility | ✅ | 51 ms |  |
| diag_01 | diagnosis | ✅ | 68 ms |  |
| diag_02 | diagnosis | ✅ | 79 ms |  |
| diag_03 | diagnosis | ✅ | 77 ms |  |
| diag_04 | diagnosis | ✅ | 83 ms |  |
| diag_05 | diagnosis | ✅ | 58 ms |  |
| diag_06 | diagnosis | ✅ | 7 ms |  |
| fuzzy_01 | search_fuzzy | ✅ | 67 ms |  |
| fuzzy_02 | search_fuzzy | ✅ | 72 ms |  |
| fuzzy_03 | search_fuzzy | ✅ | 75 ms |  |
| fuzzy_04 | search_fuzzy | ✅ | 77 ms |  |
| fuzzy_05 | search_fuzzy | ✅ | 72 ms |  |
| fuzzy_06 | search_fuzzy | ✅ | 93 ms |  |
| ground_01 | grounding | ✅ | 25 ms |  |
| ground_02 | grounding | ✅ | 40 ms |  |
| ground_03 | grounding | ✅ | 46 ms |  |
| ground_04 | grounding | ✅ | 19 ms |  |
| ground_05 | grounding | ✅ | 17 ms |  |
| inj_01 | injection | ✅ | 15 ms |  |
| inj_02 | injection | ✅ | 16 ms |  |
| inj_03 | injection | ✅ | 38 ms |  |
| inj_04 | injection | ✅ | 15 ms |  |
| scope_01 | scope | ✅ | 8 ms |  |
| scope_02 | scope | ✅ | 7 ms |  |
| scope_03 | scope | ✅ | 5 ms |  |
| scope_04 | scope | ✅ | 11 ms |  |
| scope_05 | scope | ✅ | 12 ms |  |
| scope_06 | scope | ✅ | 14 ms |  |
| scope_07 | scope | ✅ | 11 ms |  |
| scope_08 | scope | ✅ | 11 ms |  |
| spec_01 | spec_canonical | ✅ | 40 ms |  |
| spec_02 | spec_canonical | ✅ | 126 ms |  |
| spec_03 | spec_canonical | ✅ | 187 ms |  |
