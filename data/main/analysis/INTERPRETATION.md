# DAIV-LANG v001: interpretation of the main results

Numbers: [RESULTS.md](RESULTS.md), [results.json](results.json). Data: 600/600 calls,
5 blocks on 2026-10-23 UTC (`../NOTES.md`). Inference over questions (n = 30), verdicts according to
the rule in PROTOCOL.md §7. This file interprets; it does not change any number.

## Two engines, two different patterns

**Perplexity (sonar): the question language replaces almost the entire set of sources.**
- RQ1: the share of Polish-language sources for a PL question is higher by **+94 pp**
  [95% CI +88; +96] than for the same question in EN, in all three strata
  (LOCAL +91, GLOBAL +94, CONSUMER +95 pp). An effect according to §7.
- RQ2: repetitions in the same language give almost the same domains (Jaccard **0.96**),
  and PL vs EN almost none in common (**0.04**). Δoverlap +0.89 [+0.85; +0.92].
- Even in local topics, an EN question about Polish law gets mainly English-language
  sources (median PL share approx. 9%), and a PL question about global topics gets mainly
  Polish ones (median approx. 94%).
- All sensitivity analyses (without the LOCAL stratum, `unknown` in the denominator, without
  title-based detection, Jaccard on URLs) give the same direction and a similar magnitude.

**OpenAI (gpt-6-luna, API): the question language barely changes the sources, and the default
language of sources is English.**
- RQ1: median Δ = **0 pp** [0; +27]. According to the §7 rule: *no difference above noise was shown*.
  Wilcoxon (p = 0.001) indicates a shift in some of the questions, mainly LOCAL (+30 pp
  [0; +60]); in GLOBAL and CONSUMER a question in Polish still gets almost exclusively
  English-language sources (median PL share = 0).
- RQ2: agreement within the same language is low (Jaccard **0.56**), and between languages
  only slightly lower (**0.49**). Δoverlap +0.02 [+0.01; +0.06]: formally above zero,
  practically negligible. Variability between repetitions is larger than the effect of language.
- **§7 flag:** 26% of answers have no citation at all. This is almost entirely the
  GLOBAL stratum: 75/100 answers without citations (PL 38/50, EN 37/50), so for GLOBAL only
  **3/10 questions** have data in both languages. LOCAL 0/100, CONSUMER 3/100. The absence of citations does not
  depend on language. The GLOBAL results for OpenAI (API) are descriptive, not conclusive.

## RQ3 (descriptive)

- For PL questions, Perplexity cites less popular domains: share in the Tranco top 10k 32%
  (EN 58%), more domains outside the top 100k.
- OpenAI (API) cites few domains per answer (median 2 citations), and they are mainly popular
  domains (top 10k: PL 59%, EN 64%); concentration (HHI) is several times higher than for
  Perplexity.
- Because the citation construct differs (§4), we do not compare these numbers directly between
  engines; a PL vs EN comparison within an engine is allowed.

## Caveats that must go on the poster

1. **Location is not the same for both engines.** Sonar gets `country = PL`;
   for OpenAI (API) via OpenRouter it cannot be set. The difference *between* engines may
   partly result from location. The PL vs EN comparison *within* an engine is clean,
   because location is constant across both languages.
2. **Citations are different constructs:** for OpenAI they are citations embedded in the text,
   for Perplexity a list of search results.
3. **The high stability of Perplexity** (Jaccard 0.96 with blocks ≥ 60 min apart) may result
   from a search cache lasting longer than an hour. This cannot be separated with these data.
4. API via OpenRouter, not the consumer app; one day; 30 questions; one language
   pair. No conclusions about the cause (model, index, ranking) or about provider intent.
5. The language of 18% of sources was determined from the title returned by the engine (amendment 01); without this
   method the results are practically the same.
6. Manual check of the language classifier (50 URLs, §5) not yet done.

## In one sentence (working draft, EN)

*Asking the same question in Polish instead of English swaps almost the entire source set
in Perplexity (Polish-language sources +94 pp), whereas the OpenAI (API) configuration keeps citing mostly
English-language sources in both languages, except for Poland-specific topics: two
opposite ways in which AI search shapes the linguistic diversity of what users see.*

## Addendum 2026-10-24: definition of the shared-sources measure and empty sets

Checked after an external roast of the poster (no change to the analysis from §7).

- **Measure:** Jaccard of the domain sets of two answers (|A∩B| / |A∪B|). For a question: the mean over
  all pairs (within the same language: 2 × 10 pairs; PL vs EN: 25 pairs), then the median over questions.
- **Empty sets:** a pair of two answers without citations has no defined Jaccard and is
  skipped; a pair in which only one answer has citations gives 0.
- **Perplexity:** 0 empty sets (600 same-language pairs and 750 PL–EN pairs with citations),
  so 96% / 4% does not depend on this rule.
- **OpenAI:** same-language pairs: 143 both empty, 26 one empty, 431 both with citations;
  PL–EN: 179 / 32 / 539. After excluding pairs with one empty answer, the medians are 0.62
  (same language) and 0.54 (PL–EN) instead of 0.56 and 0.49. Conclusion unchanged: the difference between
  languages is small relative to the spread of repetitions.
- **No citations is not "0% Polish sources":** answers without citations are not included in the share of
  Polish-language sources (denominator = citations of known language); the absence of citations is reported
  separately (OpenAI: 26% of answers, GLOBAL stratum 75%).
