# Eval Results

- **Model:** gpt-4o  |  **Date:** 2026-06-11 02:59 UTC  |  **Git:** `9da3359`
- **Methodology:** every case replays its turns through the live SSE `/chat` API in a fresh session; a failing case is retried once (LLM nondeterminism) before being marked failed.

## Summary

| Metric | Value |
|---|---|
| Overall pass rate | **40/40 (100%)** |
| Tool-selection accuracy | 100% |
| Scope adherence | 100% |
| Hallucinated part numbers | **0** |
| Latency p50 / p95 | 2217 ms / 7906 ms |

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
| compat_01 | compatibility | ✅ | 3578 ms |  |
| compat_02 | compatibility | ✅ | 1687 ms |  |
| compat_03 | compatibility | ✅ | 1891 ms |  |
| compat_04 | compatibility | ✅ | 1733 ms |  |
| compat_05 | compatibility | ✅ | 3764 ms |  |
| compat_06 | compatibility | ✅ | 6093 ms |  |
| compat_07 | compatibility | ✅ | 2031 ms |  |
| compat_08 | compatibility | ✅ | 2733 ms |  |
| diag_01 | diagnosis | ✅ | 6391 ms |  |
| diag_02 | diagnosis | ✅ | 5750 ms |  |
| diag_03 | diagnosis | ✅ | 9157 ms |  |
| diag_04 | diagnosis | ✅ | 7906 ms |  |
| diag_05 | diagnosis | ✅ | 4875 ms |  |
| diag_06 | diagnosis | ✅ | 702 ms |  |
| fuzzy_01 | search_fuzzy | ✅ | 4608 ms |  |
| fuzzy_02 | search_fuzzy | ✅ | 4531 ms |  |
| fuzzy_03 | search_fuzzy | ✅ | 2844 ms |  |
| fuzzy_04 | search_fuzzy | ✅ | 1968 ms |  |
| fuzzy_05 | search_fuzzy | ✅ | 5671 ms |  |
| fuzzy_06 | search_fuzzy | ✅ | 3577 ms |  |
| ground_01 | grounding | ✅ | 2000 ms |  |
| ground_02 | grounding | ✅ | 1485 ms |  |
| ground_03 | grounding | ✅ | 2217 ms |  |
| ground_04 | grounding | ✅ | 1203 ms |  |
| ground_05 | grounding | ✅ | 3046 ms |  |
| inj_01 | injection | ✅ | 16 ms |  |
| inj_02 | injection | ✅ | 16 ms |  |
| inj_03 | injection | ✅ | 2625 ms |  |
| inj_04 | injection | ✅ | 717 ms |  |
| scope_01 | scope | ✅ | 718 ms |  |
| scope_02 | scope | ✅ | 593 ms |  |
| scope_03 | scope | ✅ | 0 ms |  |
| scope_04 | scope | ✅ | 703 ms |  |
| scope_05 | scope | ✅ | 1061 ms |  |
| scope_06 | scope | ✅ | 516 ms |  |
| scope_07 | scope | ✅ | 1125 ms |  |
| scope_08 | scope | ✅ | 1125 ms |  |
| spec_01 | spec_canonical | ✅ | 3733 ms |  |
| spec_02 | spec_canonical | ✅ | 6562 ms |  |
| spec_03 | spec_canonical | ✅ | 6266 ms |  |
