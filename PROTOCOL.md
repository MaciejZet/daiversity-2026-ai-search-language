# Protocol DAIV-LANG v001: query language and source diversity in AI search

**Status:** DRAFT of 2026-10-23, no data. Measurements start only after the freeze
(§10), which the author makes in a single commit.
**Goal:** poster at the 2nd dAIversity 2026, Wrocław, **3 November 2026** (UEW, inQUBE).
**Replaces:** for dAIversity, the accessibility protocol poster (BACHELOR) from
an earlier conference-materials note (internal note, not included in this repository).
That material stays in its repository unchanged.

**Working title (EN):** *Same Question, Different Sources? Query Language and Source
Diversity in AI Search: A Polish–English Pilot*

---

## 0. What was checked on 2026-10-23

| Item | Result | Source |
|---|---|---|
| Event date | 3.11.2026, registration from 9:00, start 9:30, free attendance | [event page](https://daiversity.eu/2nd-daiversity-2026-wroclaw-poland/) |
| Submission deadline, abstract limit, poster format | **Not on the page** (nor on the home page) | as above, [daiversity.eu](https://daiversity.eu/) |
| Matching programme topics | among others "Bias in large language models", inclusive technologies | as above |
| Kirsten et al., *Characterizing Web Search in The Age of Generative AI*, Findings ACL 2026 | Exists. Google organic vs 5 generative systems (Google, OpenAI, Perplexity); source diversity, instability across runs; the page does not mention multilinguality | [ACL Anthology](https://aclanthology.org/2026.findings-acl.526/) |
| Ki et al., *Linguistic Nepotism*, ICML 2026 (PMLR 306) | Exists. Controlled mRAG, 8 languages, 6 open-weight models; models prefer to cite English sources for questions asked in English | [PMLR](https://proceedings.mlr.press/v306/ki26a.html) |
| Martinez, *A Critical Survey of GEO (2023–2026)*, arXiv 2607.14035 | Exists. 45 studies; low source agreement and high variability across runs in commercial audits | [arXiv](https://arxiv.org/abs/2607.14035) |

Only the abstracts on the publishers' pages were verified. Numbers must be checked in
the full text before they are cited on the poster. The list of 8 languages in Ki et al.
(whether Polish is included) remains `[SOURCE NEEDED]`.

**For the organiser (blocks printing, not measurement):** poster format and size, whether
the poster requires prior submission or an abstract, language (we assume EN). Until we
get a reply, we provisionally assume A0 portrait.

## 1. Position relative to the literature

Kirsten et al. show that generative search engines differ in source diversity and are
unstable, but they do not study query language. Ki et al. show a language preference
in controlled mRAG on open models, where the documents are given in advance.
Our contribution is narrow: **black box, commercial products with search, the
Polish–English pair, language difference measured against a noise threshold from repeats.**

We do not claim that the difference comes from model bias. The result comes from the whole
pipeline (index, ranking, citation selection, generation), whose stages we do not separate.

## 2. Research questions

| ID | Question |
|---|---|
| **RQ1** | Does the same question asked in Polish and in English lead to a different share of Polish-language sources being cited? |
| **RQ2** | Do the lists of cited domains for PL and EN differ more than repeats of the same query differ from each other (noise threshold)? |
| **RQ3** (secondary) | Do citations concentrate on large domains, and does the concentration depend on language? |

We report each RQ separately for three topic strata (§3), because a language effect is
expected for local topics but not for global ones.

## 3. Question bank

- **N = 30 questions**, 10 per stratum:
  - **LOCAL:** topics that are inherently Polish (law, institutions, public offices, local affairs);
  - **GLOBAL:** topics with no link to a country (science, technology, general health);
  - **CONSUMER:** purchase decisions and advice, where both Polish and
    international sources exist.
- Each question has a PL and an EN version with the same meaning. The author writes PL,
  translates it into EN and checks the back-translation. In GLOBAL and CONSUMER we do not
  use terms that by themselves point to Poland (names of public offices, złoty, Polish brands).
- Informational questions, no names of private persons, no medical topics that require
  individual advice, no current politics (temporal drift).
- Working bank: [queries-draft.csv](queries-draft.csv). **Requires author approval**
  before the freeze.

## 4. Engines and conditions

We use APIs instead of the consumer interface: logs are complete, calls are repeatable,
and there is no account personalisation or manual clicking. On the poster we state
plainly that the API is not the same as the consumer product.

| Engine | Interface | What we record |
|---|---|---|
| **E1 Perplexity** | OpenRouter `perplexity/sonar`, provider Perplexity | answer, citations (`url_citation` or `citations`/`search_results`) |
| **E2 OpenAI** | OpenRouter `openai/gpt-6-luna`, provider OpenAI | answer, `url_citation` annotations |
| E3 Gemini (optional) | OpenRouter `google/gemini-3.8-flash`, Google AI Studio | as above |

**Model choice:** the default model in the consumer app, not the newest or the strongest one.
GPT-6 Luna (in the API and the desktop app since 22.09.2026), according to Notebookcheck,
has been reaching the Chat tab for Free and Go accounts since 8.10.2026; paid plans get
GPT-6 Sol
([Notebookcheck](https://notebookcheck.net/ChatGPT-Free-and-Go-users-start-getting-GPT-6-Luna-in-Chat.1419032.0.html)).
The rollout is gradual, so some free users may still have GPT-5.6 Luna
(default since 6.08.2026). The "default" status of GPT-6 Luna remains `[SOURCE NEEDED]`,
to be checked in the OpenAI release notes. Gemini 3.8 Flash is
the newest Flash; that it is the default in the Gemini app remains
`[SOURCE NEEDED]`. All three to be checked in the release notes on the day of the freeze.

**Author decision 2026-10-23: OpenRouter instead of separate provider APIs.** Every request
forces `plugins: [{"id": "web", "engine": "native"}]` and
`provider: {"order": [...], "allow_fallbacks": false}`. Without this, when native search is
unavailable, OpenRouter silently uses Exa, and the model may be served by a different host,
so we would be measuring something other than the named engine. We record the `model` and
`provider` returned by OpenRouter.

**Smoke test 2026-10-23 (36 calls):** OpenAI 12/12 ok (`openai/gpt-6-luna`, provider OpenAI,
0–8 citations, cost approx. 0.045 USD per call). Perplexity 12/12 HTTP 404: OpenRouter
rejects `engine: "native"` for Sonar, which always searches on its own. Fix: for Sonar,
no `web` plugin (not `auto`, because that would add Exa search). Gemini 12/12 HTTP 429 from
the shared Google AI Studio pool. Fix: Google AI Studio and Google Vertex both allowed
(the same model from the same provider), and on 429 up to 6 attempts with a delay of up to 120 s.
Smoke test data do not enter the analysis.

**Smoke test, second round:** Perplexity 12/12 ok (`perplexity/sonar`, provider Perplexity,
13–24 citations, approx. 0.006 USD per call). Gemini still 429: in practice the model is served
only by Google AI Studio, and the shared OpenRouter pool is exhausted. **E3 drops out of the main run**,
unless the author attaches their own Google key in OpenRouter (BYOK).

**Two observations from the smoke test that affect the analysis:**
1. **The citations of the two engines are different constructs.** OpenAI returns annotations embedded in the text
   (0–8 per answer). Perplexity returns a list of sources with `start_index = end_index = 0`, that is,
   a list of search results, not positions in the text (13–24 per answer). We **do not compare**
   absolute counts or Jaccard **across engines**; each RQ is reported separately per engine.
2. **The stability of the engines is extremely different:** domain Jaccard between two repeats of the
   same cell was 0.00–1.00 for OpenAI (URL 0.00–0.29) and 0.73–1.00 for Perplexity.
   Therefore we compute the noise threshold separately for each engine. URL-level Jaccard is computed
   only after the normalisation in §5, because OpenAI appends `?utm_source=openai`.

**Limitation:** the OpenRouter documentation does not describe `user_location` for
native search. We send `web_search_options.user_location` for Sonar; for
OpenAI and Gemini the location stays as the provider sets it. It is constant across both
languages, so it is not confounded with the language effect, but it may lower the share of
Polish sources in both versions. The direct APIs (`pplx`, `openai`) remain in the driver as an
optional variant.

E3 is in the smoke test. It enters the main run if the smoke test for E3 passes (the cost of the
additional 300 calls is low).

**Constants for all calls:**
- user location set to **Poland** in both languages, if the API allows it;
  we manipulate language only;
- no system prompt, except a minimal one identical in both languages (or none);
- default API temperature (we do not change it, so that we measure product behaviour);
- exact model ID, API version, timestamp and the full raw JSON in every record.

Parameter names (`user_location`, citation fields) must be confirmed in the documentation of both APIs
on the day of the freeze and recorded in `FREEZE.md`.

**State of the documentation on 2026-10-23:**
- **OpenAI:** `web_search` in the Responses API, `user_location` of type `approximate` with `country`,
  `include: ["web_search_call.action.sources"]` (full list of visited URLs),
  citations as `url_citation` annotations. The documentation recommends `gpt-5.5`;
  `gpt-5` with `minimal` reasoning does not support search.
- **Perplexity:** support for Sonar Chat Completions **ended on 27.09.2026**. Synchronous
  requests to `https://api.perplexity.ai/v1/sonar` work, but are being rewritten to the Agent API
  "gradually, model by model". **Risk to validity:** E1 behaviour may
  change during data collection. The driver accepts both response shapes and records
  `response_shape` for every call. If both shapes appear in the main run, we report the E1 analysis
  separately for each and describe this as a limitation. No `user_location` was found on the
  `/v1/sonar` reference page. The driver sends
  `web_search_options.user_location.country`, and the smoke test will show whether the endpoint accepts it.

**Repeats:** **R = 5** per cell (question × language × engine).
Main run: 30 × 2 × 2 × 5 = **600 calls** (+300 with E3).

**Order and time blocks (changed after the smoke test):** repeat *r* runs in a separate time
block *r* (`driver.py run ... --repeat r`), with blocks at least **60 min** apart, all
within a single day. Within a block, calls run in the random order of the plan (seed
`DAIVLANG-20261023`), in parallel with 4 threads per engine. Reason: in the smoke test, two
Perplexity repeats run ~8 s apart returned an identical list of sources in an identical order
(5/6 cells), which looks like a search cache. A noise threshold from repeats run right after
each other would measure the cache, not the variability a user experiences. Five blocks in one
day still limit index drift.

## 5. Citation processing

1. **URL normalisation:** removal of the fragment and tracking parameters (`utm_*` etc.),
   registrable domain (eTLD+1) according to the Public Suffix List.
2. **Source language is determined from content, not from the domain.** Each unique URL is fetched once
   (GET, respecting robots.txt, an ordinary research User-Agent), the main content is extracted
   (trafilatura) and the language is detected (fastText `lid.176`). Classes: `pl`, `en`, `other`,
   `unknown`. Fallback in order: the `<html lang>` attribute, then `unknown`. `.pl` domains
   are **not** automatically Polish.
3. **Quality control:** manual check of a random sample of 50 URLs (seed as above) and a record of
   classifier agreement. The share of `unknown` is reported explicitly.
4. **Domain size (RQ3):** Tranco rank from the list used in WITKP-DS (ID recorded in
   `FREEZE.md`); categories: top 10k, 10k–100k, 100k–1M, not on the list.
5. We also detect the language of the **answer**, to check whether the engine answers in the language
   of the question.

## 6. Measures

For each answer *r*:
- `n_cit(r)`: number of unique cited URLs;
- `pl_share(r)`: share of citations in the `pl` class (denominator excludes `unknown`; the variant with
  `unknown` in the denominator as a sensitivity analysis);
- `D(r)`: set of cited domains.

For a pair of answers: **domain Jaccard** J(D₁, D₂). As a complement, RBO (p = 0.9) on
ordered lists of domains.

For a cell (question × language × engine), from the pooled citations of the 5 repeats:
- number of unique domains;
- **HHI** of domain concentration;
- share of citations from Tranco top 10k domains.

## 7. Analysis (frozen before data collection)

The unit of inference is the **question** (n = 30, in strata of 10), not the individual
call. Repeats serve for averaging and for the noise threshold.

**RQ1, primary:** for each question and engine
Δpl = mean `pl_share`(PL) − mean `pl_share`(EN).
Report: median Δpl and 95% CI (bootstrap over questions, 10,000 resamples, seed as above), separately
by engine and stratum, and pooled. Auxiliary test: Wilcoxon signed-rank over questions.

**RQ2, primary:** for each question and engine
- J_within = mean Jaccard over all pairs of repeats in the same language
  (2 × 10 pairs);
- J_cross = mean Jaccard over all PL×EN pairs (25 pairs);
- **Δoverlap = J_within − J_cross.** A value > 0 means that changing the language changes
  the sources more than repetition alone does.

Report as for RQ1. J_within on its own is also a result: it shows how unstable a
single answer is.

**RQ3, secondary and descriptive:** HHI and top-10k share by language, engine and stratum,
without formal tests.

**Interpretation rules:**
- a "language effect" requires the CI for Δ to lie entirely above zero; otherwise we write
  "no difference beyond noise was shown", not "no difference";
- 30 questions is a pilot; the results do not generalise to the population of questions or to other
  language pairs;
- if an engine returns no citations in > 20% of calls, we report this as a result and compute
  the measures on the subset, noting this.

**Sensitivity analyses:** without the LOCAL stratum; `pl_share` with `unknown` in the denominator;
URL-level Jaccard instead of domain-level.

## 8. What this study does not tell us

- Nothing about the cause (model, index, ranking) or about the provider's intent.
- Nothing about users and their behaviour, or about traffic to websites.
- Nothing about the quality and credibility of the cited sources (that is topic 5 on the list, out of scope).
- The results concern the APIs in a specific week; the systems change.

## 9. Files

```
daiversity-ai-search-language-20261023-v001/
  PROTOCOL.md          this document
  queries-draft.csv    question bank, pending approval
  FREEZE.md            (after the freeze) API versions, model IDs, Tranco ID, file hashes
  code/                driver, fetcher, analysis
  data/raw/            raw JSON of every call, append-only
  data/derived/        citations, languages, measures
  poster/              poster source and export
```

API keys come only from environment variables, never from the repo.

## 10. Plan until 3 November

| Day | Task | Gate |
|---|---|---|
| Fri 23.10 | protocol, question bank (draft) | — |
| Sat 24.10 | author approves questions and translations; email to the organiser about the format | **freeze** (commit `FREEZE.md`) |
| Sun 25.10 | driver + smoke test: 3 questions × 2 languages × 2 engines × 2 repeats; smoke test data do not enter the analysis | smoke test works, citations parse |
| Mon 26.10 | **main run** (600 calls, one window) | completeness log |
| Tue 27.10 | fetch cited URLs, language, Tranco; QA of 50 URLs; optionally E3 | — |
| Wed 28.10 | analysis according to §7 | — |
| Thu–Fri 29–30.10 | poster | — |
| Sat 31.10 | review and corrections | print version |
| Mon 2.11 | printing (1 day of slack) | — |

**Poster outline:** question and motivation (language as a dimension of information diversity) →
method in one diagram → figure 1: Δpl by stratum and engine → figure 2: J_within
vs J_cross (noise threshold) → figure 3: domain concentration → limitations → QR code to the repo/data.

## 11. Open decisions for the author

1. Approval of the question bank and translations.
2. Whether E3 (Gemini) is in scope.
3. Authorship and affiliation on the poster; whether we show the connection with CometWeb.
4. Whether we publish the raw data (API responses may have licensing restrictions;
   safer: URL lists and measures, without the full answer texts).
5. API budget. The estimate for 600–900 calls is low, but it must be calculated on the day of
   the freeze using current price lists.
