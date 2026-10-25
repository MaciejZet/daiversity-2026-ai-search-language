# DAIV-LANG amendment 02: results (exploratory)

Median over questions [95% bootstrap CI], Wilcoxon as a secondary check. Δ share = A − B, Δoverlap = J_within − J_between (> 0: conditions differ more than repeats do).

## C1_location_chatgpt: A = `amend:openai`, B = `amend:openai-noloc`

| Query language | Stratum | Δ Polish share (A − B) | Δoverlap |
|---|---|---|---|
| PL | LOCAL | +0 pp [+0 pp; +0 pp], n=10 | +0.00 [-0.15; +0.00], n=10, p=0.438 |
| PL | GLOBAL | +0 pp [+0 pp; +0 pp], n=2 | +0.00 [+0.00; +0.50], n=4 |
| PL | CONSUMER | +25 pp [+8 pp; +54 pp], n=10, p=0.00781 | +0.06 [-0.03; +0.24], n=10, p=0.109 |
| PL | ALL | +0 pp [+0 pp; +0 pp], n=22, p=0.0273 | +0.00 [+0.00; +0.00], n=24, p=0.32 |
| EN | LOCAL | +0 pp [-4 pp; +14 pp], n=10, p=0.469 | +0.00 [-0.02; +0.12], n=10, p=0.812 |
| EN | GLOBAL | +0 pp [+0 pp; +0 pp], n=2 | +0.00 [-0.04; +0.00], n=3 |
| EN | CONSUMER | +0 pp [+0 pp; +50 pp], n=9 | +0.12 [+0.00; +0.35], n=10, p=0.0391 |
| EN | ALL | +0 pp [+0 pp; +12 pp], n=21, p=0.0605 | +0.00 [+0.00; +0.08], n=23, p=0.0382 |

PL: J_within 0.39, J_between 0.33.

EN: J_within 0.42, J_between 0.46.

## C2_path_chatgpt: A = `amend:openai-noloc`, B = `amend:or-openai`

| Query language | Stratum | Δ Polish share (A − B) | Δoverlap |
|---|---|---|---|
| PL | LOCAL | +0 pp [+0 pp; +0 pp], n=10 | +0.00 [-0.14; +0.00], n=10, p=0.125 |
| PL | GLOBAL | +0 pp [+0 pp; +0 pp], n=2 | +0.00 [-0.21; +1.00], n=3 |
| PL | CONSUMER | +0 pp [-25 pp; +12 pp], n=10, p=0.75 | -0.06 [-0.17; +0.17], n=10, p=0.891 |
| PL | ALL | +0 pp [+0 pp; +0 pp], n=22, p=0.75 | +0.00 [-0.12; +0.00], n=23, p=0.432 |
| EN | LOCAL | +0 pp [-5 pp; +20 pp], n=10, p=0.469 | +0.00 [+0.00; +0.17], n=10, p=0.188 |
| EN | GLOBAL | +0 pp [+0 pp; +0 pp], n=3 | -0.17 [-0.33; +0.00], n=3 |
| EN | CONSUMER | +0 pp [+0 pp; +0 pp], n=10 | -0.08 [-0.17; +0.02], n=10, p=0.0859 |
| EN | ALL | +0 pp [+0 pp; +0 pp], n=23, p=0.266 | +0.00 [-0.03; +0.00], n=23, p=0.478 |

PL: J_within 0.46, J_between 0.50.

EN: J_within 0.53, J_between 0.58.

## C3_location_perplexity: A = `amend:or-pplx`, B = `amend:or-pplx-noloc`

| Query language | Stratum | Δ Polish share (A − B) | Δoverlap |
|---|---|---|---|
| PL | LOCAL | +0 pp [+0 pp; +0 pp], n=10 | +0.00 [-0.02; +0.00], n=10 |
| PL | GLOBAL | +0 pp [-0 pp; +1 pp], n=10 | -0.01 [-0.05; +0.00], n=10, p=0.0625 |
| PL | CONSUMER | +0 pp [-1 pp; +0 pp], n=10 | -0.04 [-0.08; -0.03], n=10, p=0.00391 |
| PL | ALL | +0 pp [+0 pp; +0 pp], n=30, p=0.938 | -0.03 [-0.04; +0.00], n=30, p=0.000436 |
| EN | LOCAL | +0 pp [+0 pp; +0 pp], n=10 | +0.00 [+0.00; +0.00], n=10 |
| EN | GLOBAL | +0 pp [+0 pp; +0 pp], n=10 | +0.00 [-0.00; +0.00], n=10 |
| EN | CONSUMER | +0 pp [+0 pp; +0 pp], n=10 | -0.01 [-0.06; +0.00], n=10, p=0.0625 |
| EN | ALL | +0 pp [+0 pp; +0 pp], n=30 | +0.00 [+0.00; +0.00], n=30, p=0.0117 |

PL: J_within 0.94, J_between 0.97.

EN: J_within 1.00, J_between 1.00.

## T1_day_perplexity: A = `main:or-pplx`, B = `amend:or-pplx`

| Query language | Stratum | Δ Polish share (A − B) | Δoverlap |
|---|---|---|---|
| PL | LOCAL | +0 pp [+0 pp; +0 pp], n=10 | +0.16 [+0.01; +0.21], n=10, p=0.0117 |
| PL | GLOBAL | +0 pp [-1 pp; +3 pp], n=10, p=0.688 | +0.05 [+0.01; +0.19], n=10, p=0.0117 |
| PL | CONSUMER | +0 pp [-6 pp; +0 pp], n=10, p=0.219 | +0.07 [+0.02; +0.15], n=10, p=0.00781 |
| PL | ALL | +0 pp [+0 pp; +0 pp], n=30, p=0.414 | +0.08 [+0.03; +0.13], n=30, p=3.77e-06 |
| EN | LOCAL | +0 pp [+0 pp; +4 pp], n=10 | +0.12 [+0.00; +0.27], n=10, p=0.0312 |
| EN | GLOBAL | +0 pp [+0 pp; +0 pp], n=10 | +0.08 [-0.01; +0.19], n=10, p=0.0391 |
| EN | CONSUMER | +0 pp [+0 pp; +0 pp], n=10 | +0.09 [+0.07; +0.23], n=10, p=0.00195 |
| EN | ALL | +0 pp [+0 pp; +0 pp], n=30 | +0.09 [+0.06; +0.16], n=30, p=2.86e-05 |

PL: J_within 0.93, J_between 0.82.

EN: J_within 0.98, J_between 0.85.

## T2_day_chatgpt: A = `main:or-openai`, B = `amend:or-openai`

| Query language | Stratum | Δ Polish share (A − B) | Δoverlap |
|---|---|---|---|
| PL | LOCAL | +0 pp [+0 pp; +0 pp], n=10 | +0.00 [-0.02; +0.03], n=10, p=0.688 |
| PL | GLOBAL | +0 pp [+0 pp; +0 pp], n=3 | -0.18 [-0.20; +0.01], n=3 |
| PL | CONSUMER | -5 pp [-19 pp; +0 pp], n=10, p=0.0938 | +0.04 [+0.02; +0.08], n=10, p=0.0488 |
| PL | ALL | +0 pp [+0 pp; +0 pp], n=23, p=0.219 | +0.01 [+0.00; +0.04], n=23, p=0.245 |
| EN | LOCAL | +0 pp [-5 pp; +15 pp], n=10, p=0.688 | +0.00 [-0.06; +0.01], n=10, p=0.578 |
| EN | GLOBAL | +0 pp [+0 pp; +0 pp], n=3 | +0.02 [-0.08; +0.23], n=3 |
| EN | CONSUMER | +0 pp [+0 pp; +0 pp], n=10 | +0.07 [-0.02; +0.10], n=10, p=0.129 |
| EN | ALL | +0 pp [+0 pp; +0 pp], n=23, p=0.469 | +0.01 [+0.00; +0.07], n=23, p=0.314 |

PL: J_within 0.41, J_between 0.40.

EN: J_within 0.66, J_between 0.56.

## RQ1 (PL − EN) in each amendment condition

| Condition | Δ Polish share (ALL) | without citations (PL/GLOBAL, EN/GLOBAL) | responses |
|---|---|---|---|
| ChatGPT direct API, country=PL | +17 pp [+0 pp; +25 pp], n=21, p=0.000244 | 70%, 80% | 120 |
| ChatGPT direct API, no location | +0 pp [+0 pp; +28 pp], n=22, p=0.00391 | 80%, 75% | 120 |
| ChatGPT via OpenRouter, no location | +10 pp [+0 pp; +25 pp], n=23, p=0.000488 | 70%, 75% | 120 |
| Perplexity, country=PL | +94 pp [+90 pp; +95 pp], n=30, p=1.64e-06 | 0%, 0% | 120 |
| Perplexity, no location | +94 pp [+89 pp; +95 pp], n=30, p=1.64e-06 | 0%, 0% | 120 |
