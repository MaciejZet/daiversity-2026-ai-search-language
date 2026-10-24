# DAIV-LANG v001: results

Data: `data/main/derived`. Bootstrap 10000 resamples, seed `DAIVLANG-20261023`. Median over questions [95% CI], Wilcoxon test as a secondary check. Verdict per protocol §7: CI entirely above zero = effect; otherwise "not shown".

## Perplexity (sonar, API)

Responses 300, citations 5757, median citations 18, without citations 0%, source language unknown 5%, answer in the query language 100%.

| Stratum | RQ1 Δ Polish share (PL − EN) | RQ2 Δoverlap (J_within − J_cross) | Δ RBO |
|---|---|---|---|
| LOCAL | +91 pp [+87 pp; +100 pp], n=10, p=0.00195 | +0.85 [+0.77; +0.93], n=10, p=0.00195 | +0.80 [+0.61; +0.87], n=10, p=0.00195 |
| GLOBAL | +94 pp [+81 pp; +100 pp], n=10, p=0.00195 | +0.94 [+0.90; +0.97], n=10, p=0.00195 | +0.97 [+0.87; +0.98], n=10, p=0.00195 |
| CONSUMER | +95 pp [+71 pp; +96 pp], n=10, p=0.00195 | +0.84 [+0.72; +0.90], n=10, p=0.00195 | +0.92 [+0.85; +0.94], n=10, p=0.00195 |
| ALL | +94 pp [+88 pp; +96 pp], n=30, p=1.64e-06 | +0.89 [+0.85; +0.92], n=30, p=1.73e-06 | +0.89 [+0.84; +0.93], n=30, p=1.86e-09 |

Verdicts (ALL): RQ1 above zero; RQ2 above zero.

**Sensitivity analyses (ALL):**

- rq1_unknown_in_denominator: +90 pp [+87 pp; +94 pp], n=30, p=1.73e-06
- rq1_only_text_html_methods: +93 pp [+86 pp; +100 pp], n=30, p=1.51e-06
- rq1_without_LOCAL: +95 pp [+83 pp; +95 pp], n=20, p=8.68e-05
- rq2_url_level: +0.92 [+0.88; +0.97], n=30, p=1.71e-06
- rq2_without_LOCAL: +0.90 [+0.85; +0.93], n=20, p=1.91e-06

**RQ3 (descriptive; cells = question × language, pooled over repeats):**

| Language/stratum | median unique domains | median HHI | median top-10k share |
|---|---|---|---|
| pl/LOCAL | 12 | 0.115 | 22% |
| pl/GLOBAL | 16 | 0.077 | 39% |
| pl/CONSUMER | 20 | 0.066 | 38% |
| pl/ALL | 16 | 0.094 | 29% |
| en/LOCAL | 11 | 0.131 | 40% |
| en/GLOBAL | 12 | 0.117 | 79% |
| en/CONSUMER | 18 | 0.081 | 62% |
| en/ALL | 12 | 0.107 | 60% |

## OpenAI (gpt-6-luna, API)

Responses 300, citations 620, median citations 2, without citations 26% **(> 20%, §7 flag)**, source language unknown 3%, answer in the query language 100%.

| Stratum | RQ1 Δ Polish share (PL − EN) | RQ2 Δoverlap (J_within − J_cross) | Δ RBO |
|---|---|---|---|
| LOCAL | +30 pp [+0 pp; +60 pp], n=10, p=0.0156 | +0.02 [+0.00; +0.22], n=10, p=0.0156 | +0.00 [-0.04; +0.14], n=10, p=0.438 |
| GLOBAL | +0 pp [+0 pp; +0 pp], n=3 | +0.01 [-0.10; +0.08], n=3 | -0.08 [-0.10; +0.01], n=3 |
| CONSUMER | +0 pp [+0 pp; +17 pp], n=10 | +0.02 [-0.00; +0.06], n=10, p=0.129 | +0.03 [+0.01; +0.08], n=10, p=0.0371 |
| ALL | +0 pp [+0 pp; +27 pp], n=23, p=0.000977 | +0.02 [+0.01; +0.06], n=23, p=0.01 | +0.01 [+0.00; +0.03], n=23, p=0.182 |

Verdicts (ALL): RQ1 no difference beyond noise shown; RQ2 above zero.

**Sensitivity analyses (ALL):**

- rq1_unknown_in_denominator: +0 pp [+0 pp; +27 pp], n=23, p=0.000977
- rq1_only_text_html_methods: +0 pp [+0 pp; +27 pp], n=23, p=0.00195
- rq1_without_LOCAL: +0 pp [+0 pp; +7 pp], n=13
- rq2_url_level: +0.02 [+0.01; +0.05], n=23, p=0.00927
- rq2_without_LOCAL: +0.02 [+0.00; +0.06], n=13, p=0.204

**RQ3 (descriptive; cells = question × language, pooled over repeats):**

| Language/stratum | median unique domains | median HHI | median top-10k share |
|---|---|---|---|
| pl/LOCAL | 4 | 0.656 | 25% |
| pl/GLOBAL | 2 | 0.514 | 100% |
| pl/CONSUMER | 5 | 0.266 | 62% |
| pl/ALL | 4 | 0.389 | 53% |
| en/LOCAL | 2 | 0.620 | 39% |
| en/GLOBAL | 2 | 0.755 | 100% |
| en/CONSUMER | 4 | 0.342 | 85% |
| en/ALL | 3 | 0.488 | 83% |

Engines are not compared in absolute numbers: OpenAI returns inline citations, Perplexity a list of search results (PROTOCOL.md, smoke run).
