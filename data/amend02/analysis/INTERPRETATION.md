# Amendment 02: interpretation (exploratory)

Data: 600/600 calls, no errors, two blocks on 2026-10-25 UTC, 65 min apart, about two days after
the main run. Verdicts follow the rules fixed in `FREEZE.md` before data collection.

| Contrast | Result (all questions) | Verdict |
|---|---|---|
| C1: OpenAI direct, country=PL vs no location (Polish query) | +0 pp [+0; +0] | no location effect shown |
| C2: OpenAI direct vs OpenRouter | all CIs include 0 | OpenRouter and the direct API give consistent sources |
| C3: Perplexity, country=PL vs no location (Polish query) | +0 pp [+0; +0] | no location effect shown |
| T1: Perplexity, day 1 vs day 3 | Δoverlap PL +0.08 [+0.03; +0.13], EN +0.09 [+0.06; +0.16] | sources change more across days than within a day |
| T2: OpenAI, day 1 vs day 3 | CIs touch 0 | not shown |

The Polish-source effect in Perplexity comes from the query language, not the location: +94 pp
(PL vs EN) with and without location. Across days Perplexity's shared sources drop from 93–98% to
82–85%, still far above the 4% shared between languages. Exploratory: for consumer questions asked
in Polish, location PL raised OpenAI's Polish-source share by +25 pp [+8; +54] (n = 10). Two
repeats per condition; location is an API parameter, not a real IP.
