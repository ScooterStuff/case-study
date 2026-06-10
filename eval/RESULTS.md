# Eval Results

- **Model:** MOCK  |  **Date:** 2026-06-10 22:22 UTC  |  **Git:** `257eafa`
- **Methodology:** every case replays its turns through the live SSE `/chat` API in a fresh session; a failing case is retried once (LLM nondeterminism) before being marked failed.

## Summary

| Metric | Value |
|---|---|
| Overall pass rate | **40/40 (100%)** |
| Tool-selection accuracy | 100% |
| Scope adherence | 100% |
| Hallucinated part numbers | **0** |
| Latency p50 / p95 | 31 ms / 111 ms |

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
| compat_01 | compatibility | ✅ | 58 ms |  |
| compat_02 | compatibility | ✅ | 41 ms |  |
| compat_03 | compatibility | ✅ | 29 ms |  |
| compat_04 | compatibility | ✅ | 21 ms |  |
| compat_05 | compatibility | ✅ | 27 ms |  |
| compat_06 | compatibility | ✅ | 71 ms |  |
| compat_07 | compatibility | ✅ | 39 ms |  |
| compat_08 | compatibility | ✅ | 44 ms |  |
| diag_01 | diagnosis | ✅ | 44 ms |  |
| diag_02 | diagnosis | ✅ | 67 ms |  |
| diag_03 | diagnosis | ✅ | 111 ms |  |
| diag_04 | diagnosis | ✅ | 76 ms |  |
| diag_05 | diagnosis | ✅ | 87 ms |  |
| diag_06 | diagnosis | ✅ | 6 ms |  |
| fuzzy_01 | search_fuzzy | ✅ | 82 ms |  |
| fuzzy_02 | search_fuzzy | ✅ | 55 ms |  |
| fuzzy_03 | search_fuzzy | ✅ | 72 ms |  |
| fuzzy_04 | search_fuzzy | ✅ | 59 ms |  |
| fuzzy_05 | search_fuzzy | ✅ | 82 ms |  |
| fuzzy_06 | search_fuzzy | ✅ | 70 ms |  |
| ground_01 | grounding | ✅ | 6 ms |  |
| ground_02 | grounding | ✅ | 30 ms |  |
| ground_03 | grounding | ✅ | 31 ms |  |
| ground_04 | grounding | ✅ | 5 ms |  |
| ground_05 | grounding | ✅ | 7 ms |  |
| inj_01 | injection | ✅ | 2 ms |  |
| inj_02 | injection | ✅ | 2 ms |  |
| inj_03 | injection | ✅ | 15 ms |  |
| inj_04 | injection | ✅ | 7 ms |  |
| scope_01 | scope | ✅ | 3 ms |  |
| scope_02 | scope | ✅ | 3 ms |  |
| scope_03 | scope | ✅ | 3 ms |  |
| scope_04 | scope | ✅ | 3 ms |  |
| scope_05 | scope | ✅ | 2 ms |  |
| scope_06 | scope | ✅ | 3 ms |  |
| scope_07 | scope | ✅ | 3 ms |  |
| scope_08 | scope | ✅ | 2 ms |  |
| spec_01 | spec_canonical | ✅ | 35 ms |  |
| spec_02 | spec_canonical | ✅ | 107 ms |  |
| spec_03 | spec_canonical | ✅ | 136 ms |  |
