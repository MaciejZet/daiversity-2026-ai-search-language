"""Offline tests for sources.py (fake fetcher and detector; no network, no fastText model).
Needs the isolated venv: data/cache/venv/bin/python -m unittest discover -s code/tests"""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
DEPS = all(importlib.util.find_spec(m) for m in ("tldextract", "trafilatura"))
if DEPS:
    import sources  # noqa: E402

PL_TEXT = "To jest polski tekst o szczepionkach. " * 10
HTML_PL = f"<!doctype html><html lang='pl'><body><article><p>{PL_TEXT}</p></article></body></html>"


def fake_detect(text):
    return ("pl", 0.99) if ("polski" in text or "Jak" in text) else ("en", 0.95)


class FakeFetcher:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def allowed(self, url):
        return "blocked" not in url

    def get(self, url):
        self.calls.append(url)
        return self.pages[url]


@unittest.skipUnless(DEPS, "needs data/cache/venv (tldextract, trafilatura)")
class SourcesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_normalize_and_domain(self):
        u = sources.normalize_url("HTTPS://Www.CDC.gov/a.html?CDC_AA_refVal=x&utm_source=openai&id=3#f")
        self.assertEqual(u, "https://www.cdc.gov/a.html?id=3")
        self.assertEqual(sources.registered_domain("uk.pcmag.com"), "pcmag.com")
        self.assertEqual(sources.registered_domain("www.gov.pl"), "www.gov.pl")  # gov.pl is a public suffix
        self.assertEqual(sources.registered_domain("psse.gov.pl"), "psse.gov.pl")

    def test_language_chain(self):
        d = sources.decide_language(PL_TEXT, "en", "Title", fake_detect)
        self.assertEqual((d["src_lang"], d["src_lang_method"]), ("pl", "text"))
        d = sources.decide_language("short", "pl-PL", None, fake_detect)
        self.assertEqual((d["src_lang"], d["src_lang_method"]), ("pl", "html"))
        d = sources.decide_language(None, None, "Jak założyć działalność gospodarczą", fake_detect)
        self.assertEqual((d["src_lang"], d["src_lang_method"]), ("pl", "title"))
        d = sources.decide_language(None, "de", None, fake_detect)
        self.assertEqual(d["src_lang"], "other")
        self.assertEqual(sources.decide_language(None, None, "short", fake_detect)["src_lang"], "unknown")

    def test_fetch_cache_enrich_and_qa(self):
        cites = self.tmp / "cit.jsonl"
        rows = [
            {"slot_id": "G01-pl-or-pplx-r0", "qid": "G01", "stratum": "GLOBAL", "lang": "pl",
             "engine": "or-pplx", "repeat": 0, "answer_text": PL_TEXT, "model_returned": "m",
             "citations": [{"url": "https://www.mp.pl/a?utm_source=x", "title": None},
                           {"url": "https://www.mp.pl/a", "title": None},
                           {"url": "https://x.org/doc.pdf", "title": "About mRNA vaccines today"},
                           {"url": "https://blocked.com/p", "title": "Jak działa szczepionka mRNA"},
                           {"url": "https://err.com/p", "title": None}]}]
        cites.write_text("\n".join(json.dumps(r) for r in rows))
        f = FakeFetcher({
            "https://www.mp.pl/a": {"http_status": 200, "content_type": "text/html; charset=utf-8",
                                    "charset": "utf-8", "body": HTML_PL.encode()},
            "https://x.org/doc.pdf": {"http_status": 200, "content_type": "application/pdf",
                                      "body": b"%PDF-1.4"},
            "https://err.com/p": {"http_status": 403, "error": "HTTP 403"},
        })
        cache = self.tmp / "cache"
        pages = self.tmp / "pages.jsonl"
        s = sources.fetch([cites], pages, cache, 2, fetcher=f, detect=fake_detect)
        self.assertEqual(s["urls"], 4)
        by = {json.loads(l)["url_norm"]: json.loads(l) for l in pages.read_text().splitlines()}
        self.assertEqual(by["https://www.mp.pl/a"]["src_lang_method"], "text")
        self.assertEqual(by["https://x.org/doc.pdf"]["fetch_status"], "not_html")
        self.assertEqual(by["https://x.org/doc.pdf"]["src_lang"], "en")
        self.assertEqual(by["https://blocked.com/p"]["fetch_status"], "robots_disallowed")
        self.assertEqual(by["https://blocked.com/p"]["src_lang"], "pl")
        self.assertEqual(by["https://err.com/p"]["src_lang"], "unknown")

        n = len(f.calls)
        sources.fetch([cites], pages, cache, 2, fetcher=f, detect=fake_detect)
        self.assertEqual(len(f.calls), n)  # cached, nothing refetched
        sources.fetch([cites], pages, cache, 2, fetcher=f, detect=fake_detect, retry_errors=True)
        self.assertEqual(f.calls[n:], ["https://err.com/p"])

        tranco = self.tmp / "t.csv"
        tranco.write_text("1,google.com\n5000,mp.pl\n200000,x.org\n")
        out = self.tmp / "out"
        s = sources.enrich([cites], pages, tranco, out, detect=fake_detect)
        self.assertEqual((s["responses"], s["citations"], s["citations_not_fetched"]), (1, 4, 0))
        cited = [json.loads(l) for l in (out / "cited.jsonl").read_text().splitlines()]
        self.assertEqual([c["tranco_bin"] for c in cited], ["top10k", "100k-1M", "unlisted", "unlisted"])
        self.assertEqual([c["rank_in_answer"] for c in cited], [0, 1, 2, 3])
        resp = json.loads((out / "responses.jsonl").read_text())
        self.assertEqual((resp["n_cit"], resp["answer_lang"]), (4, "pl"))

        qa = self.tmp / "qa.csv"
        sources.qa_sample(out / "cited.jsonl", qa, 3)
        self.assertEqual(len(qa.read_text().splitlines()), 4)


if __name__ == "__main__":
    unittest.main()
