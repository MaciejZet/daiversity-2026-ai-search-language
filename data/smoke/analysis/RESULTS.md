# DAIV-LANG v001: results

Data: `data/smoke/derived`. Bootstrap 2000 resamples, seed `DAIVLANG-20261023`. Median over questions [95% CI], Wilcoxon test as a secondary check. Verdict per protocol §7: CI entirely above zero = effect; otherwise "not shown".

## Perplexity (sonar, API)

Responses 12, citations 224, median citations 18, without citations 0%, source language unknown 3%, answer in the query language 100%.

| Stratum | RQ1 Δ Polish share (PL − EN) | RQ2 Δoverlap (J_within − J_cross) | Δ RBO |
|---|---|---|---|
| LOCAL | +100 pp [+100 pp; +100 pp], n=1 | +0.96 [+0.96; +0.96], n=1 | +0.84 [+0.84; +0.84], n=1 |
| GLOBAL | +94 pp [+94 pp; +94 pp], n=1 | +1.00 [+1.00; +1.00], n=1 | +1.00 [+1.00; +1.00], n=1 |
| CONSUMER | +62 pp [+62 pp; +62 pp], n=1 | +0.72 [+0.72; +0.72], n=1 | +0.52 [+0.52; +0.52], n=1 |
| ALL | +94 pp [+94 pp; +94 pp], n=3 | +0.96 [+0.96; +0.96], n=3 | +0.84 [+0.84; +0.84], n=3 |

Verdicts (ALL): RQ1 above zero; RQ2 above zero.

**Sensitivity analyses (ALL):**

- rq1_unknown_in_denominator: +94 pp [+94 pp; +94 pp], n=3
- rq1_only_text_html_methods: +100 pp [+100 pp; +100 pp], n=3
- rq1_without_LOCAL: +78 pp [+78 pp; +78 pp], n=2
- rq2_url_level: +1.00 [+1.00; +1.00], n=3
- rq2_without_LOCAL: +0.86 [+0.86; +0.86], n=2

**RQ3 (descriptive; cells = question × language, pooled over repeats):**

| Language/stratum | median unique domains | median HHI | median top-10k share |
|---|---|---|---|
| pl/LOCAL | 14 | 0.114 | 21% |
| pl/GLOBAL | 13 | 0.105 | 39% |
| pl/CONSUMER | 17 | 0.069 | 42% |
| pl/ALL | 14 | 0.105 | 39% |
| en/LOCAL | 13 | 0.094 | 0% |
| en/GLOBAL | 11 | 0.112 | 62% |
| en/CONSUMER | 14 | 0.103 | 82% |
| en/ALL | 13 | 0.103 | 62% |

## OpenAI (gpt-6-luna, API)

Responses 12, citations 34, median citations 2, without citations 8%, source language unknown 3%, answer in the query language 100%.

| Stratum | RQ1 Δ Polish share (PL − EN) | RQ2 Δoverlap (J_within − J_cross) | Δ RBO |
|---|---|---|---|
| LOCAL | +32 pp [+32 pp; +32 pp], n=1 | +0.00 [+0.00; +0.00], n=1 | -0.07 [-0.07; -0.07], n=1 |
| GLOBAL | +0 pp [+0 pp; +0 pp], n=1 | +0.00 [+0.00; +0.00], n=1 | +0.00 [+0.00; +0.00], n=1 |
| CONSUMER | +50 pp [+50 pp; +50 pp], n=1 | +0.25 [+0.25; +0.25], n=1 | +0.50 [+0.50; +0.50], n=1 |
| ALL | +32 pp [+32 pp; +32 pp], n=3 | +0.00 [+0.00; +0.00], n=3 | +0.00 [+0.00; +0.00], n=3 |

Verdicts (ALL): RQ1 above zero; RQ2 no difference beyond noise shown.

**Sensitivity analyses (ALL):**

- rq1_unknown_in_denominator: +25 pp [+25 pp; +25 pp], n=3
- rq1_only_text_html_methods: +32 pp [+32 pp; +32 pp], n=3
- rq1_without_LOCAL: +25 pp [+25 pp; +25 pp], n=2
- rq2_url_level: +0.33 [+0.33; +0.33], n=3
- rq2_without_LOCAL: +0.12 [+0.12; +0.12], n=2

**RQ3 (descriptive; cells = question × language, pooled over repeats):**

| Language/stratum | median unique domains | median HHI | median top-10k share |
|---|---|---|---|
| pl/LOCAL | 3 | 0.449 | 13% |
| pl/GLOBAL | 2 | 0.625 | 100% |
| pl/CONSUMER | 2 | 0.556 | 100% |
| pl/ALL | 2 | 0.556 | 100% |
| en/LOCAL | 3 | 0.506 | 11% |
| en/GLOBAL | 1 | 1.000 | 100% |
| en/CONSUMER | 1 | 1.000 | 0% |
| en/ALL | 1 | 1.000 | 11% |

Engines are not compared in absolute numbers: OpenAI returns inline citations, Perplexity a list of search results (PROTOCOL.md, smoke run).
