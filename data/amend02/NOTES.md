# Amendment 02 log

## Smoke test, 2026-10-24

- 6 slots (`data/amend02/smoke/plan.json`). `openai` and `openai-noloc` 4/4 ok: returned model
  `gpt-6-luna` through the direct Responses API, 6–9 `url_citation` annotations, 39–63 sources in
  `web_search_call.action.sources`. **C1 and C2 stay** (the condition in FREEZE is met).
- `or-pplx-noloc` 0/2: `OPENROUTER_API_KEY` was not set in the author's shell; the driver's worker
  thread ended silently and the summary reported `failed: 0`. Technical fix to the driver: a missing
  key now stops `run` before the first call (test `test_missing_key_fails_before_any_call`). Call
  logic and request content unchanged; `code/driver.py` SHA-256 after the fix
  `a2fa112fe5a31ca9d7eb9e9bf7ce71cab5d99e67b9cf02d2e91ec911769221ed`
  (frozen in Amendment 02: `fc81891a…`).
- Smoke test of `or-pplx-noloc` to be repeated with both keys before block 0.
- Second smoke round: first 2 × HTTP 401 (`or-pplx-noloc`; the shell held a literal placeholder
  `...` instead of the key; the `*.err-0.json` records are kept). With the keys set correctly 2/2 ok:
  `perplexity/sonar` through Perplexity, 16–20 citations. **Smoke test complete, 6/6.**
- Observation (smoke test, not analysed): question L01 gives mainly biznes.gov.pl in both OpenAI
  direct conditions; Perplexity without location still cites the `/en/` pages of biznes.gov.pl for
  the English query, as in the main run with location.

## Technical change, 2026-10-24 (before the amendment blocks)

- Report strings in `code/analyze.py` and `code/amend02.py` translated into English for the public
  repository. Computation unchanged: re-running `analyze.py` on the main data gives an identical
  `results.json` apart from the verdict text (checked programmatically).
- `code/amend02.py` SHA-256 after the change:
  `ff1807f133a2a2e7f9dea3e155cb298fb2ffe17d6f6b223e15e71f33d61871d8`
  (frozen in Amendment 02: `faafac89…`).
