# Source language classification check (PROTOCOL.md §5, item 3)

**Date:** 2026-10-26. **Sample:** 50 URLs drawn from the main `cited.jsonl` (seed `DAIVLANG-20261023-QA`,
`sources.py qa-sample`); file [`qa-sample.csv`](qa-sample.csv), columns `manual_lang` and `note`.

**Who and how:** the check was done by an AI assistant from a snippet of the page text (trafilatura
extract of the saved HTML) and the title returned by the engine, independently of the fastText
classifier. It is not a human rating.

## Result

| | Count |
|---|---|
| URLs in the sample | 50 |
| with a language assigned by the classifier | 48 |
| agreeing with the check | **48 / 48 (100%)** |
| `unknown` in the classifier | 2 (4%; 4.6% in the whole set) |

With 48/48 agreeing, the 95% Clopper–Pearson interval for accuracy is about 93–100%.

Both `unknown` items have no readable content (HTTP 403 or empty page): #22 (Forbes) is in fact
English, #44 (study.gov.pl, `/pl/` path) is most likely Polish but cannot be confirmed. The
`unknown` rule is conservative rather than wrong.

## Caveats

- **"title" method (10 of 48):** the check used the same title as the classifier because the page
  text was not available, so it is not independent for these items; the 38 items classified from
  page text or `<html lang>` are.
- The sample is small: it shows no systematic error, not the absence of individual mistakes.

## Observations

- Two pages on `.pl` domains are in English (#45 zpe.gov.pl, #46 warszawa19115.pl): classifying by
  content rather than by domain matters.
- Interface fragments in another language (#36 Russian, #47 Chinese) did not change the correct
  classification of the article.
