# Same question, different language, different sources

Data, code and protocol behind a poster for the 2nd dAIversity Conference (Wrocław University of
Economics and Business, 3 November 2026).

**Research question:** does the language of a query change the sources that AI search engines cite?

**Author:** Maciej Zmitrukiewicz, Wrocław University of Economics and Business
(194034@student.ue.wroc.pl)

## Summary

A pilot study with 30 questions, each asked in Polish and in English, 5 times, in two AI search
configurations accessed through APIs on 23 October 2026: Perplexity `sonar` and OpenAI
`gpt-6-luna` with web search, both via OpenRouter.

In Perplexity, two answers in the same language share a median of 96% of their cited domains,
while a Polish and an English answer share 4%. In the OpenAI configuration the language changes the
sources only slightly (56% vs 49%), and 26% of answers cite nothing. This is a pilot: it does not
assess answer quality and does not explain why the sources differ.

| | Perplexity (sonar, API) | OpenAI (gpt-6-luna, API) |
|---|---|---|
| Shared sources, same language (median over questions) | 96% | 56% |
| Shared sources, Polish vs English | 4% | 49% |
| Polish-language share of sources, PL / EN query, topics other than Poland-specific | 95% / 0% | 0% / 0% |
| Answers without any citation | 0% | 26% (global facts: 75%) |

Full results with confidence intervals: [`data/main/analysis/RESULTS.md`](data/main/analysis/RESULTS.md).
Interpretation and caveats: [`data/main/analysis/INTERPRETATION.md`](data/main/analysis/INTERPRETATION.md).

**"Shared sources"** is the Jaccard index of the two answers' sets of cited domains (shared / all),
averaged over all answer pairs for a question, then the median over the 30 questions. A pair of two
answers without citations is skipped; a pair where only one answer has citations counts as 0. See
`INTERPRETATION.md` for the effect of this rule.

## Repository contents

| Path | Contents |
|---|---|
| `PROTOCOL.md` | study protocol, written before data collection |
| `FREEZE.md` | freeze record: file hashes, configuration, amendments 01 and 02 with reasons |
| `queries-draft.csv` | the 30 questions in Polish and English (version accepted before the main run) |
| `code/driver.py` | API data collection (plan, run, citation extraction) |
| `code/sources.py` | URL normalization, page fetching, source language (fastText), Tranco rank |
| `code/analyze.py` | analysis as specified in protocol §7, figures |
| `code/amend02.py` | amendment 02 analysis (location, access path, stability across days) |
| `code/poster_figs.py` | poster figures from `results.json` |
| `code/tests/` | offline tests (`python3 -m unittest discover -s code/tests`) |
| `data/main/plan.json` | the 600 planned calls with order and seed |
| `data/main/NOTES.md` | collection log, including the aborted and repeated block 4 |
| `data/main/citations.jsonl` | citations of each answer (URL, title, rank), model, timestamp |
| `data/main/derived/pages.jsonl` | the 1,584 cited pages: fetch status, language and how it was determined |
| `data/main/derived/cited.jsonl` | one row per citation: domain, source language, Tranco rank |
| `data/main/derived/responses.jsonl` | one row per answer: number of citations, answer language |
| `data/main/derived/qa-sample.csv` | random sample of 50 URLs for a manual language check |
| `data/main/analysis/` | `RESULTS.md`, `results.json`, interpretation, figures |
| `data/amend02/` | amendment 02 plan, smoke test and log (data collection pending) |
| `data/smoke/` | trial run before the freeze (not analysed) |
| `poster/` | poster source (Polish), preview and QR code |

### What is not included, and why

- **Raw API responses and full answer texts.** They contain snippets of third-party pages taken
  from search results. The repository keeps the citations, their classification and every measure
  needed to reproduce the analysis. Raw responses are available to researchers on request.
- **Contents of fetched pages.** Only metadata and the language classification.
- **API keys.** The code reads them from environment variables.

## Reproducing the analysis

```bash
uv venv --python 3.12 data/cache/venv
uv pip install --python data/cache/venv/bin/python trafilatura fasttext-wheel "numpy<2" tldextract scipy matplotlib
data/cache/venv/bin/python code/analyze.py data/main/derived data/main/analysis
```

Running the analysis on the published derived data reproduces `results.json` exactly. The full
pipeline from scratch (new API calls, about 15 USD) is described in the docstrings of `driver.py`
and `sources.py`; it needs `OPENROUTER_API_KEY`, the fastText model `lid.176.ftz` and the Tranco
list `56Z8N` (hashes in `FREEZE.md`). Search engine answers change over time, so a new run will
produce different raw data.

## Limitations

Pilot: 30 questions, one language pair, one day, access through APIs rather than the consumer apps.
The location was set to Poland only for Perplexity, so each configuration is compared only with
itself. The citations of the two systems are different constructs (OpenAI: inline references;
Perplexity: a list of search results). The study does not assess answer quality and does not
explain where the differences come from. Amendment 02 (2026-10-25) found no location effect in either system, consistent sources
between OpenRouter and the direct OpenAI API, and Perplexity again at +94 pp two days later; see
`data/amend02/analysis/INTERPRETATION.md`.

## Language note

The study was run and first documented in Polish. Documentation, code comments and reports in this
repository are English translations; the question bank keeps both languages because the questions
are the data. The poster in `poster/` is in Polish, as presented at the conference.

## License

Code: MIT (`LICENSE`). Data, protocol and text: CC BY 4.0. Titles and URLs of cited pages belong to
their publishers.
