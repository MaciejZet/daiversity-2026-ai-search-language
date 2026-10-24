"""Offline tests with fake API responses. Run: python3 -m unittest discover -s code/tests"""
import json
import os
import tempfile
import unittest
from unittest import mock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import driver  # noqa: E402

QUERIES = Path(__file__).resolve().parents[2] / "queries-draft.csv"

PPLX_OK = {"model": "sonar", "choices": [{"message": {"content": "Odpowiedź [1]."}}],
           "citations": ["https://a.pl/x", "https://b.com/y"],
           "search_results": [{"url": "https://a.pl/x", "title": "A"},
                              {"url": "https://b.com/y", "title": "B"}]}
OPENAI_OK = {"model": "gpt-5-2026", "output": [
    {"type": "web_search_call", "action": {"sources": [{"url": "https://c.org/1"},
                                                       {"url": "https://d.pl/2"}]}},
    {"type": "message", "content": [{"type": "output_text", "text": "Answer.",
     "annotations": [{"type": "url_citation", "url": "https://c.org/1", "title": "C"},
                     {"type": "url_citation", "url": "https://c.org/1", "title": "C"},
                     {"type": "url_citation", "url": "https://d.pl/2", "title": "D"}]}]}]}


def fake_post(url, key, body):
    return 200, PPLX_OK if "perplexity" in url else OPENAI_OK


def make_plan(tmp_path):
    slots = driver.build_plan(driver.load_queries(QUERIES), ["pplx", "openai"], 2,
                              ["L01", "G01", "C01"])
    p = tmp_path / "plan.json"
    p.write_text(json.dumps({"slots": slots, "plan_sha256": "test"}))
    return p


KEYS = {"PERPLEXITY_API_KEY": "SECRETKEY123", "OPENAI_API_KEY": "SECRETKEY123"}


@mock.patch.dict(os.environ, KEYS)
@mock.patch.object(driver.time, "sleep", lambda s: None)
class DriverTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.plan = make_plan(self.tmp)
        self.root = self.tmp / "run"

    def tearDown(self):
        self._tmp.cleanup()

    def test_plan_shape_and_determinism(self):
        qs = driver.load_queries(QUERIES)
        self.assertEqual(len(qs), 30)
        a = driver.build_plan(qs, ["pplx", "openai"], 5)
        self.assertEqual(a, driver.build_plan(qs, ["pplx", "openai"], 5))
        self.assertEqual(len({s["slot_id"] for s in a}), 600)
        self.assertNotEqual([s["slot_id"] for s in a[:8]],
                            sorted(s["slot_id"] for s in a[:8]))

    def test_run_resume_and_extract(self):
        self.assertEqual(driver.run(self.plan, self.root, 5, 0, post=fake_post)["ok_new"], 5)
        s2 = driver.run(self.plan, self.root, None, 0, post=fake_post)
        self.assertEqual((s2["ok_new"], s2["already_present"]), (19, 5))
        for f in (self.root / "raw").glob("*.json"):
            self.assertNotIn("SECRETKEY123", f.read_text())
        out = self.tmp / "cit.jsonl"
        self.assertEqual(driver.extract(self.root, out), 24)
        rows = [json.loads(l) for l in out.read_text().splitlines()]
        o = next(r for r in rows if r["engine"] == "openai")
        self.assertEqual([c["url"] for c in o["citations"]], ["https://c.org/1", "https://d.pl/2"])
        self.assertEqual(o["search_sources"], ["https://c.org/1", "https://d.pl/2"])
        self.assertEqual(o["model_returned"], "gpt-5-2026")
        p = next(r for r in rows if r["engine"] == "pplx")
        self.assertEqual([c["url"] for c in p["citations"]], ["https://a.pl/x", "https://b.com/y"])

    def test_retry_then_error_kept_and_retried(self):
        calls = []

        def flaky(url, key, body):
            calls.append(1)
            return 429, {"error": "rate"}

        self.assertEqual(driver.run(self.plan, self.root, 1, 0, post=flaky)["failed"], 1)
        self.assertEqual(len(calls), driver.MAX_ATTEMPTS_429)
        self.assertEqual(len(list((self.root / "raw").glob("*.err-0.json"))), 1)
        self.assertEqual(driver.run(self.plan, self.root, 1, 0, post=fake_post)["ok_new"], 1)

    def test_server_error_uses_short_retry_limit(self):
        calls = []

        def down(url, key, body):
            calls.append(1)
            return 503, {"error": "down"}

        driver.run(self.plan, self.root, 1, 0, post=down)
        self.assertEqual(len(calls), driver.MAX_ATTEMPTS)

    def test_parallel_workers_and_engine_filter(self):
        s = driver.run(self.plan, self.root, None, 0, post=fake_post,
                       workers={"pplx": 3}, engines={"pplx"})
        self.assertEqual(s["ok_new"], 12)
        s = driver.run(self.plan, self.root, None, 0, post=fake_post,
                       workers={"pplx": 3, "openai": 3})
        self.assertEqual((s["ok_new"], s["already_present"]), (12, 12))
        ledger = (self.root / "ledger.jsonl").read_text().splitlines()
        self.assertEqual(len(ledger), 24)
        self.assertEqual(len({json.loads(l)["slot_id"] for l in ledger}), 24)

    def test_repeat_filter(self):
        s = driver.run(self.plan, self.root, None, 0, post=fake_post, repeats={0})
        self.assertEqual(s["ok_new"], 12)
        self.assertTrue(all(f.name.endswith("-r0.json") for f in (self.root / "raw").glob("*.json")))

    def test_amendment02_location_variants(self):
        loc = driver.ENGINES["openai"]["build"]("Q")
        noloc = driver.ENGINES["openai-noloc"]["build"]("Q")
        self.assertEqual(loc["tools"][0]["user_location"]["country"], "PL")
        self.assertNotIn("user_location", noloc["tools"][0])
        self.assertEqual(loc["model"], noloc["model"])
        self.assertEqual(loc["include"], ["web_search_call.action.sources"])
        pp = driver.ENGINES["or-pplx-noloc"]["build"]("Q")
        self.assertNotIn("web_search_options", pp)
        self.assertNotIn("plugins", pp)
        base = driver.ENGINES["or-pplx"]["build"]("Q")
        base.pop("web_search_options")
        self.assertEqual(base, pp)

    def test_missing_key_fails_before_any_call(self):
        calls = []
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            with self.assertRaises(SystemExit):
                driver.run(self.plan, self.root, None, 0,
                           post=lambda *a: calls.append(1) or (200, PPLX_OK))
        self.assertEqual(calls, [])

    def test_bad_request_not_retried(self):
        calls = []

        def bad(url, key, body):
            calls.append(1)
            return 400, {"error": "bad param"}

        driver.run(self.plan, self.root, 1, 0, post=bad)
        self.assertEqual(len(calls), 1)


    def test_pplx_agent_shape(self):
        resp = {"object": "response", "model": "sonar", "output": [
            {"type": "search_results", "results": [{"id": 1, "url": "https://e.pl/1"},
                                                   {"id": 2, "url": "https://f.com/2"}]},
            {"type": "message", "content": [{"type": "output_text", "text": "Tekst"}]}]}
        text, cites, model, shape = driver.extract_pplx(resp)
        self.assertEqual((text, model, shape), ("Tekst", "sonar", "response"))
        self.assertEqual([c["url"] for c in cites], ["https://e.pl/1", "https://f.com/2"])
        self.assertEqual(driver.extract_pplx(PPLX_OK)[3], "chat.completion")


    def test_openrouter_request_and_extract(self):
        body = driver.ENGINES["or-openai"]["build"]("Q")
        self.assertEqual(body["plugins"], [{"id": "web", "engine": "native"}])
        self.assertEqual(body["provider"], {"order": ["OpenAI"], "allow_fallbacks": False})
        pplx = driver.ENGINES["or-pplx"]["build"]("Q")
        self.assertIn("user_location", pplx["web_search_options"])
        self.assertNotIn("plugins", pplx)
        self.assertEqual(driver.ENGINES["or-gemini"]["build"]("Q")["provider"]["order"],
                         ["Google AI Studio", "Google Vertex"])
        resp = {"model": "openai/gpt-5.5", "provider": "OpenAI", "choices": [{"message": {
            "content": "A [x](https://g.pl/1)",
            "annotations": [
                {"type": "url_citation", "url_citation": {"url": "https://g.pl/1", "title": "G"}},
                {"type": "url_citation", "url_citation": {"url": "https://g.pl/1", "title": "G"}},
                {"type": "url_citation", "url_citation": {"url": "https://h.com/2"}}]}}]}
        text, cites, model, sources = driver.extract_openrouter(resp)
        self.assertEqual([c["url"] for c in cites], ["https://g.pl/1", "https://h.com/2"])
        self.assertIsNone(sources)
        pp = {"choices": [{"message": {"content": "B"}}], "citations": ["https://i.pl"]}
        self.assertEqual(driver.extract_openrouter(pp)[3], ["https://i.pl"])


if __name__ == "__main__":
    unittest.main()
