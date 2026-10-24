"""Offline test of analyze.py on synthetic data with a known answer.
Needs the isolated venv (numpy, scipy): data/cache/venv/bin/python -m unittest discover -s code/tests"""
import importlib.util
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
DEPS = all(importlib.util.find_spec(m) for m in ("numpy", "scipy"))
if DEPS:
    import analyze  # noqa: E402


def synthetic(tmp: Path):
    """PL queries cite only Polish domains, EN only English ones; repeats identical.
    Expected: delta_pl = +1 for every question, J_within = 1, J_cross = 0."""
    cited, resp = [], []
    for s_i, stratum in enumerate(analyze.STRATA):
        for q in range(10):
            qid = f"{stratum[0]}{q:02d}"
            for lang in ("pl", "en"):
                for r in range(5):
                    slot = f"{qid}-{lang}-or-pplx-r{r}"
                    resp.append({"slot_id": slot, "qid": qid, "stratum": stratum,
                                 "query_lang": lang, "engine": "or-pplx", "repeat": r,
                                 "answer_lang": lang, "n_cit": 3})
                    for k in range(3):
                        cited.append({"slot_id": slot, "rank_in_answer": k,
                                      "url_norm": f"https://{lang}{k}.{qid}.example/",
                                      "domain": f"{lang}{k}-{qid}.example", "src_lang": lang,
                                      "src_lang_method": "text",
                                      "tranco_bin": "top10k" if k == 0 else "unlisted"})
    (tmp / "cited.jsonl").write_text("\n".join(json.dumps(c) for c in cited))
    (tmp / "responses.jsonl").write_text("\n".join(json.dumps(r) for r in resp))


@unittest.skipUnless(DEPS, "needs data/cache/venv (numpy, scipy)")
class AnalyzeTest(unittest.TestCase):
    def test_rbo_and_jaccard(self):
        self.assertAlmostEqual(analyze.rbo(list("abcde"), list("abcde")), 1.0)
        self.assertEqual(analyze.rbo(list("abc"), list("xyz")), 0.0)
        self.assertTrue(math.isnan(analyze.jaccard(set(), set())))
        self.assertEqual(analyze.pl_share([{"src_lang": "pl", "src_lang_method": "text"},
                                           {"src_lang": "unknown", "src_lang_method": "none"}]), 1.0)
        self.assertEqual(analyze.pl_share([{"src_lang": "pl", "src_lang_method": "text"},
                                           {"src_lang": "unknown", "src_lang_method": "none"}],
                                          unknown_in_denominator=True), 0.5)

    def test_known_answer(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            synthetic(d)
            res = analyze.analyze(d, d / "out", n_boot=200, make_figures=True)
            e = res["engines"]["or-pplx"]
            self.assertEqual(e["rq1"]["ALL"]["n"], 30)
            self.assertAlmostEqual(e["rq1"]["ALL"]["median"], 1.0)
            self.assertEqual(e["rq1"]["ALL"]["verdict"], "above zero")
            self.assertAlmostEqual(e["rq2_levels"]["j_within"]["median"], 1.0)
            self.assertAlmostEqual(e["rq2_levels"]["j_cross"]["median"], 0.0)
            self.assertAlmostEqual(e["rq3_concentration"]["pl/ALL"]["median_top10k_share"], 1 / 3)
            self.assertEqual(e["descriptives"]["answer_in_query_language"], 1.0)
            self.assertTrue((d / "out" / "fig2_overlap.png").exists())
            self.assertIn("LOCAL", (d / "out" / "RESULTS.md").read_text())


if __name__ == "__main__":
    unittest.main()
