# DAIV-LANG v001: freeze before main

**Date:** 2026-10-23. The author approved the question bank and the schedule of time blocks.
The commit containing this file is the freeze point: changes to questions, engines, models,
measures or analysis rules after this commit are amendments, recorded with a date and a reason.

## Frozen files (SHA-256)

| File | SHA-256 |
|---|---|
| `PROTOCOL.md` | `b9d3ac52032245ba17acaabd2d98e41690f31fd10f0efe5f707cf418eade8891` |
| `queries-draft.csv` (approved, the name stays) | `2b2497f2c11bb45cfb9cafae29d598d73c5e751a1e1c2e354d1127be878e846d` |
| `code/driver.py` | `468bee3711d51d1081f0624debd03effd2f1300a89672f47a893f08d7f0361ab` |
| `data/main/plan.json` | `540d708729da0953c254f486aa625bfe7eef0d35cc97cfcdbf434570f7a33964` |

`plan_sha256` (hash of the slot list, stored in every record):
`310c74da754bc21c86238b231151b8b72a199efa7e5419b437bff44cd848a914`.

## Main configuration

| Item | Value |
|---|---|
| Engines | `or-openai` (`openai/gpt-6-luna`, provider OpenAI, `plugins: web/native`), `or-pplx` (`perplexity/sonar`, provider Perplexity, no plugin) |
| Dropped | `or-gemini` (HTTP 429 from the shared pool in the smoke test); returns only as an amendment with BYOK |
| Plan | 30 questions × 2 languages × 2 engines × 5 repetitions = 600 slots, seed `DAIVLANG-20261023` |
| Blocks | `--repeat r` for r = 0..4, ≥ 60 min apart, one day |
| Threads | 4 per engine (default `--workers`) |
| Location | `web_search_options.user_location.country = PL` for Sonar only; OpenAI without location |
| Tranco (RQ3) | list `56Z8N` from 2026-10-22 (the same as WITKP-DS; metadata: internal note, not included in this repository) |

## To check at the start of block 0 (record in `data/main/NOTES.md`)

- whether the default models in the apps (GPT-6 Luna for ChatGPT Free) have not changed;
- `model` and `provider` returned in the first records match the table above.

Smoke data (`data/smoke/`) stays in the repo as a record of the driver qualification and is not
part of the analysis.

## Amendment 01 (2026-10-23, before block 0, no main data)

`code/sources.py` implements §5 with three clarifications, set on the smoke data:

1. **An additional level in the language chain:** content (fastText on text from trafilatura, ≥ 200
   characters, p ≥ 0.5) → `<html lang>` → **title returned by the engine** (fastText, ≥ 20 characters)
   → `unknown`. Reason: in the smoke test, 12/127 pages returned HTTP 403 for a plain research
   User-Agent, and 7 were PDFs. Without the title they would be `unknown`. The method is recorded
   for each source; the sensitivity analysis from §7 gets a "only `text` and `html`" variant.
2. **Domain = eTLD+1 according to the PSL** from the snapshot built into tldextract (no network). `gov.pl` is
   a public suffix, so `biznes.gov.pl`, `podatki.gov.pl` and `www.gov.pl` are separate
   domains (separate institutions).
3. **Environment:** a separate venv `data/cache/venv` (Python 3.12, trafilatura 2.3.1,
   fasttext-wheel, tldextract), certificates from certifi.

| Artifact | SHA-256 |
|---|---|
| `data/cache/lid.176.ftz` (fastText, dl.fbaipublicfiles.com) | `8f3472cfe8738a7b6099e8e999c3cbfae0dcd15696aac7d7738a8039db603e83` |
| `data/cache/tranco/top-1m.csv` (Tranco `56Z8N`, `download_daily/56Z8N`) | `bf3103bb0dec409876e02c753319dbe7a95f775a26142170e10d159fd183587a` |

`data/cache/` is not included in the repo (size, third-party content). The hashes above allow the data to be reproduced.

Smoke run through the whole pipeline: 127 unique URLs, 108 fetched, 12 × 403, 7 non-HTML;
language: 64 pl, 58 en, 1 other, 4 unknown (3%); method: 108 text, 15 title, 4 none.

## Amendment 02 (2026-10-24, after main, before collecting the amendment data)

**Status: exploratory.** The main results (RQ1–RQ3, `data/main/analysis/`) remain unchanged
regardless of the outcome of this amendment. The amendment addresses two caveats from
`data/main/analysis/INTERPRETATION.md`: (1) the location `country=PL` was set only for
Perplexity, (2) the stability of Perplexity (Jaccard 0.96) may be due to caching.

**Conditions (all in the same run, so location comparisons are from the same day):**

| Engine in the driver | Access | Location |
|---|---|---|
| `openai` | direct Responses API, `gpt-6-luna`, `web_search` | `country=PL` |
| `openai-noloc` | as above | none |
| `or-openai` | OpenRouter, as in main | none (as in main) |
| `or-pplx` | OpenRouter, as in main | `country=PL` (as in main) |
| `or-pplx-noloc` | OpenRouter, Sonar | none |

**Plan:** 30 questions × 2 languages × 5 conditions × 2 repetitions = 600 slots
(`data/amend02/plan.json`, `plan_sha256` `0779cb024304e41be4030bd32c790077fdce0c95636b38c8627752bea1969697`,
seed as in main). Two blocks, `--repeat 0` and `--repeat 1`, ≥ 60 min apart, **both on 2026-10-25
(UTC)**, i.e. about 2 days after main. Before block 0, a smoke test of 6 calls to the new engines
(`data/amend02/smoke/plan.json`), outside the analysis. Estimated cost about 18 USD.

**Contrasts (`code/amend02.py`), per question, separately for the question language:**

| ID | A | B | What it resolves |
|---|---|---|---|
| C1 | `openai` | `openai-noloc` | whether the PL location changes the sources of OpenAI (API) |
| C2 | `openai-noloc` | `or-openai` | whether OpenRouter gives the same as the direct API |
| C3 | `or-pplx` | `or-pplx-noloc` | whether the "Polishness" of Perplexity is due to location |
| T1 | `or-pplx` main (day 1) | `or-pplx` amendment (day 3) | stability of Perplexity across days |
| T2 | `or-openai` main | `or-openai` amendment | stability of OpenAI (API) across days |

Measures: Δ share of PL sources (A − B) and Δoverlap = J_within − J_between (mean Jaccard
within conditions minus between conditions). Median over questions, 95% bootstrap CI
(10,000, stratified), Wilcoxon as a supplementary test. In addition, RQ1 (PL − EN) and the share of answers without
citations in each condition.

**Wording rules for the poster (set before the data):**
- C1/C3: CI of Δ share (PL question, ALL) entirely > 0 → "location increases the share of Polish
  sources"; otherwise "no effect of location was shown". If C1 shows an effect, we describe the
  OpenAI (API) vs Perplexity difference from main as partly dependent on location.
- C2: both CIs (Δ share and Δoverlap, ALL) include 0 → "OpenRouter and the direct API give
  consistent sources"; otherwise we report the path difference as a limitation.
- T1/T2: CI of Δoverlap entirely > 0 → "sources change more between days than within a
  day"; this resolves whether the high stability of Perplexity in main was a single-day phenomenon.
- C1 with OpenAI direct requires the `OPENAI_API_KEY` key; if the smoke test shows that `gpt-6-luna`
  is not available in the direct API, C1/C2 are dropped (recorded in NOTES), C3/T1/T2 remain.

Tests: `code/tests/test_driver.py::test_amendment02_location_variants`; a null test of
`amend02.py` (repetitions 0–1 vs 2–3 of main as two pseudo-conditions) gave Δ = 0, CI around 0.

| File | SHA-256 |
|---|---|
| `code/driver.py` | `fc81891aab19687c0757e88e6a431c75e07cafc6500185521f921f3f7e584c86` |
| `code/amend02.py` | `faafac89ee538fbbc18563d6be6d9ce5844bfdc520474c3fdd97b1bb0582c74e` |
| `data/amend02/plan.json` | `f629b37f1183262533c85615b9326310b50e9f32fa5bb326320a014ce0242a6f` |
