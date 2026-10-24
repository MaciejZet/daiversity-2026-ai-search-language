"""DAIV-LANG v001 collection driver (protocol §4). Standard library only.

usage:
  driver.py plan QUERIES.csv OUT_PLAN.json [--repeats 5] [--engines pplx,openai] [--qids L01,G01,C01]
  driver.py run PLAN.json RUN_ROOT [--max N] [--sleep 1.0] [--workers or-openai=4,...] [--engines ...]
  driver.py extract RUN_ROOT OUT_CITATIONS.jsonl

Engines: or-openai, or-pplx, or-gemini go through OpenRouter (OPENROUTER_API_KEY) with
provider-native search forced and provider fallbacks off, so a silent Exa fallback or a
different host cannot replace the engine under test. pplx and openai call the vendor APIs
directly (PERPLEXITY_API_KEY, OPENAI_API_KEY). OpenRouter model slugs: DAIV_OR_OPENAI_MODEL
(default "openai/gpt-6-luna"), DAIV_OR_PPLX_MODEL ("perplexity/sonar"), DAIV_OR_GEMINI_MODEL
("google/gemini-3.8-flash"). Models from DAIV_PPLX_MODEL
(default "sonar") and DAIV_OPENAI_MODEL (default "gpt-6-luna"); the model id returned by the API
is what the analysis uses.

Each slot writes one raw JSON file to RUN_ROOT/raw/{slot_id}.json (request without key,
full response, HTTP status, timestamps). An existing file with status "ok" is never
rewritten, so a stopped run resumes by running again. Failed slots are kept as
raw/{slot_id}.err-{n}.json and retried on the next run.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import queue
import random
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCHEDULE_SEED = "DAIVLANG-20261023"
LANGS = ("pl", "en")
COUNTRY = "PL"
TIMEOUT_S = 120
RETRY_STATUSES = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 3
MAX_ATTEMPTS_429 = 6  # upstream shared-pool rate limits (smoke 2026-10-23, Gemini)

# Sonar Chat Completions support ended 2026-09-27; sync requests to /v1/sonar are being
# reformulated as Agent API requests, so both response shapes are accepted and recorded.
PPLX_URL = "https://api.perplexity.ai/v1/sonar"
OPENAI_URL = "https://api.openai.com/v1/responses"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------- plan

def load_queries(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_plan(queries: list[dict], engines: list[str], repeats: int,
               qids: list[str] | None = None) -> list[dict]:
    if qids:
        queries = [q for q in queries if q["qid"] in qids]
    slots = []
    for q in queries:
        for lang in LANGS:
            for eng in engines:
                for r in range(repeats):
                    slots.append({
                        "slot_id": f"{q['qid']}-{lang}-{eng}-r{r}",
                        "qid": q["qid"], "stratum": q["stratum"], "lang": lang,
                        "engine": eng, "repeat": r, "query": q[f"q_{lang}"],
                    })
    rng = random.Random(int(hashlib.sha256(SCHEDULE_SEED.encode()).hexdigest(), 16))
    rng.shuffle(slots)
    for i, s in enumerate(slots):
        s["order"] = i
    return slots


# ---------------------------------------------------------------- engines

def pplx_request(query: str) -> dict:
    return {
        "model": os.environ.get("DAIV_PPLX_MODEL", "sonar"),
        "messages": [{"role": "user", "content": query}],
        "web_search_options": {"user_location": {"country": COUNTRY}},
    }


def openai_request(query: str, location: bool = True) -> dict:
    tool = {"type": "web_search"}
    if location:
        tool["user_location"] = {"type": "approximate", "country": COUNTRY}
    return {
        "model": os.environ.get("DAIV_OPENAI_MODEL", "gpt-6-luna"),
        "input": query,
        "tools": [tool],
        "include": ["web_search_call.action.sources"],
    }


def openrouter_request(model_env: str, default: str, providers: list[str],
                       extra: dict | None = None, native_plugin: bool = True):
    """native_plugin=False for models that always search (Perplexity Sonar): OpenRouter
    rejects engine "native" for them, and "auto" would add an Exa search on top."""
    def build(query: str) -> dict:
        body = {
            "model": os.environ.get(model_env, default),
            "messages": [{"role": "user", "content": query}],
            "provider": {"order": providers, "allow_fallbacks": False},
        }
        if native_plugin:
            body["plugins"] = [{"id": "web", "engine": "native"}]
        body.update(extra or {})
        return body
    return build


ENGINES = {
    "pplx": {"url": PPLX_URL, "key": "PERPLEXITY_API_KEY", "build": pplx_request},
    "openai": {"url": OPENAI_URL, "key": "OPENAI_API_KEY", "build": openai_request},
    # Amendment 02 (location check): direct OpenAI with and without country=PL, and
    # Perplexity Sonar through OpenRouter without the location option.
    "openai-noloc": {"url": OPENAI_URL, "key": "OPENAI_API_KEY",
                     "build": lambda q: openai_request(q, location=False)},
    "or-openai": {"url": OPENROUTER_URL, "key": "OPENROUTER_API_KEY",
                  "build": openrouter_request("DAIV_OR_OPENAI_MODEL", "openai/gpt-6-luna", ["OpenAI"])},
    "or-pplx": {"url": OPENROUTER_URL, "key": "OPENROUTER_API_KEY",
                "build": openrouter_request(
                    "DAIV_OR_PPLX_MODEL", "perplexity/sonar", ["Perplexity"],
                    {"web_search_options": {"user_location": {"country": COUNTRY}}},
                    native_plugin=False)},
    "or-pplx-noloc": {"url": OPENROUTER_URL, "key": "OPENROUTER_API_KEY",
                      "build": openrouter_request("DAIV_OR_PPLX_MODEL", "perplexity/sonar",
                                                  ["Perplexity"], native_plugin=False)},
    "or-gemini": {"url": OPENROUTER_URL, "key": "OPENROUTER_API_KEY",
                  "build": openrouter_request("DAIV_OR_GEMINI_MODEL", "google/gemini-3.8-flash",
                                              ["Google AI Studio", "Google Vertex"])},
}


def post_json(url: str, key: str, body: dict) -> tuple[int, dict | str]:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        text = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(text)
        except json.JSONDecodeError:
            return e.code, text


def call_slot(slot: dict, post=post_json) -> dict:
    eng = ENGINES[slot["engine"]]
    key = os.environ.get(eng["key"])
    if not key:
        raise SystemExit(f"{eng['key']} is not set")
    body = eng["build"](slot["query"])
    attempts = []
    attempt = 0
    while True:
        t0 = now()
        mono = time.monotonic()
        try:
            status, payload = post(eng["url"], key, body)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            status, payload = None, f"{type(e).__name__}: {e}"
        attempts.append({"started": t0, "elapsed_s": round(time.monotonic() - mono, 3),
                         "http_status": status})
        if status == 200 and isinstance(payload, dict):
            return {"slot": slot, "status": "ok", "request": body, "response": payload,
                    "attempts": attempts}
        if status is not None and status not in RETRY_STATUSES:
            break
        attempt += 1
        limit = MAX_ATTEMPTS_429 if status == 429 else MAX_ATTEMPTS
        if attempt >= limit:
            break
        time.sleep(min(2 ** attempt * 10, 120) if status == 429 else 2 ** attempt * 5)
    return {"slot": slot, "status": "error", "request": body, "response": payload,
            "attempts": attempts}


def run(plan_path: Path, root: Path, max_calls: int | None, sleep_s: float,
        post=post_json, workers: dict[str, int] | None = None,
        engines: set[str] | None = None, repeats: set[int] | None = None) -> dict:
    """Runs engines in parallel (rate limits are per engine), each engine with
    workers[engine] threads (default 1) taking its slots in plan order."""
    plan = json.loads(plan_path.read_text())
    raw = root / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    ledger = root / "ledger.jsonl"
    lock = threading.Lock()
    counts = {"ok_new": 0, "failed": 0, "already_present": 0}
    queues: dict[str, queue.Queue] = {}
    for slot in plan["slots"]:
        if engines and slot["engine"] not in engines:
            continue
        if repeats is not None and slot["repeat"] not in repeats:
            continue
        if (raw / f"{slot['slot_id']}.json").exists():
            counts["already_present"] += 1
            continue
        queues.setdefault(slot["engine"], queue.Queue()).put(slot)

    reserved = [0]

    def take(q: queue.Queue):
        with lock:
            if max_calls is not None and reserved[0] >= max_calls:
                return None
            try:
                slot = q.get_nowait()
            except queue.Empty:
                return None
            reserved[0] += 1
            return slot

    def worker(q: queue.Queue):
        while (slot := take(q)) is not None:
            rec = call_slot(slot, post)
            rec["plan_sha256"] = plan["plan_sha256"]
            with lock:
                if rec["status"] == "ok":
                    (raw / f"{slot['slot_id']}.json").write_text(
                        json.dumps(rec, ensure_ascii=False, indent=1))
                    counts["ok_new"] += 1
                else:
                    n = len(list(raw.glob(f"{slot['slot_id']}.err-*.json")))
                    (raw / f"{slot['slot_id']}.err-{n}.json").write_text(
                        json.dumps(rec, ensure_ascii=False, indent=1))
                    counts["failed"] += 1
                with ledger.open("a") as f:
                    f.write(json.dumps({"t": now(), "slot_id": slot["slot_id"],
                                        "status": rec["status"],
                                        "http": rec["attempts"][-1]["http_status"]}) + "\n")
                print(f"[{slot['order']:>4}] {slot['slot_id']:<24} {rec['status']}", flush=True)
            time.sleep(sleep_s)

    missing = sorted({ENGINES[e]["key"] for e in queues if not os.environ.get(ENGINES[e]["key"])})
    if missing:  # fail before any call: a missing key inside a worker thread used to end
        raise SystemExit(f"not set: {', '.join(missing)}")  # that thread silently
    threads = [threading.Thread(target=worker, args=(q,), daemon=True)
               for eng, q in queues.items() for _ in range((workers or {}).get(eng, 1))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    summary = {**counts, "planned": len(plan["slots"])}
    print(json.dumps(summary))
    return summary


# ---------------------------------------------------------------- extract

def extract_pplx(resp: dict) -> tuple[str, list[dict], str | None, str]:
    """Returns text, citations, model, shape ("chat.completion" or "response")."""
    if resp.get("object") == "response" or "output" in resp:
        texts, cites = [], []
        for item in resp.get("output", []):
            if item.get("type") == "search_results":
                cites += [{"url": r.get("url"), "title": r.get("title"), "rank": len(cites) + i}
                          for i, r in enumerate(item.get("results") or []) if r.get("url")]
            if item.get("type") == "message":
                texts += [c.get("text", "") for c in item.get("content", [])
                          if c.get("type") == "output_text"]
        return "\n".join(texts), cites, resp.get("model"), "response"
    text = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
    results = resp.get("search_results") or []
    if results:
        cites = [{"url": r.get("url"), "title": r.get("title"), "rank": i}
                 for i, r in enumerate(results) if r.get("url")]
    else:
        cites = [{"url": u, "title": None, "rank": i}
                 for i, u in enumerate(resp.get("citations") or [])]
    return text, cites, resp.get("model"), "chat.completion"


def extract_openai(resp: dict) -> tuple[str, list[dict], str | None]:
    texts, cites, seen = [], [], set()
    sources = []
    for item in resp.get("output", []):
        if item.get("type") == "web_search_call":
            for s in (item.get("action") or {}).get("sources") or []:
                if s.get("url"):
                    sources.append(s["url"])
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    texts.append(c.get("text", ""))
                    for a in c.get("annotations", []):
                        if a.get("type") == "url_citation" and a.get("url") not in seen:
                            seen.add(a["url"])
                            cites.append({"url": a["url"], "title": a.get("title"),
                                          "rank": len(cites)})
    return "\n".join(texts), cites, resp.get("model"), sources


def extract_openrouter(resp: dict) -> tuple[str, list[dict], str | None, list | None]:
    """Chat Completions shape: url_citation annotations; Perplexity may also pass through
    top-level search_results/citations, kept as search_sources."""
    msg = (resp.get("choices") or [{}])[0].get("message", {})
    cites, seen = [], set()
    for a in msg.get("annotations") or []:
        if a.get("type") != "url_citation":
            continue
        uc = a.get("url_citation") or a
        if uc.get("url") and uc["url"] not in seen:
            seen.add(uc["url"])
            cites.append({"url": uc["url"], "title": uc.get("title"), "rank": len(cites)})
    sources = [r.get("url") for r in resp.get("search_results") or [] if r.get("url")] \
        or resp.get("citations") or None
    if not cites and sources:  # Perplexity may return sources without inline annotations
        cites = [{"url": u, "title": None, "rank": i} for i, u in enumerate(sources)]
    return msg.get("content") or "", cites, resp.get("model"), sources


def extract(root: Path, out: Path) -> int:
    rows = 0
    with out.open("w", encoding="utf-8") as f:
        for p in sorted((root / "raw").glob("*.json")):
            if ".err-" in p.name:
                continue
            rec = json.loads(p.read_text())
            slot, resp = rec["slot"], rec["response"]
            sources = None
            if slot["engine"] == "pplx":  # direct Perplexity API (not used in main)
                text, cites, model, shape = extract_pplx(resp)
            elif slot["engine"].startswith("or-"):
                text, cites, model, sources = extract_openrouter(resp)
                shape = "chat.completion"
            else:
                text, cites, model, sources = extract_openai(resp)
                shape = "response"
            f.write(json.dumps({
                "slot_id": slot["slot_id"], "qid": slot["qid"], "stratum": slot["stratum"],
                "lang": slot["lang"], "engine": slot["engine"], "repeat": slot["repeat"],
                "model_returned": model, "provider_returned": resp.get("provider"),
                "response_shape": shape, "answer_text": text, "citations": cites,
                "search_sources": sources, "started": rec["attempts"][-1]["started"],
            }, ensure_ascii=False) + "\n")
            rows += 1
    print(f"{rows} responses -> {out}")
    return rows


# ---------------------------------------------------------------- cli

def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("queries", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--repeats", type=int, default=5)
    p.add_argument("--engines", default="or-openai,or-pplx")
    p.add_argument("--qids", default=None)
    r = sub.add_parser("run")
    r.add_argument("plan", type=Path)
    r.add_argument("root", type=Path)
    r.add_argument("--max", type=int, default=None)
    r.add_argument("--sleep", type=float, default=1.0)
    r.add_argument("--workers", default="or-openai=4,or-pplx=4,or-gemini=1",
                   help="threads per engine, e.g. or-openai=4,or-gemini=1")
    r.add_argument("--engines", default=None, help="run only these engines")
    r.add_argument("--repeat", default=None,
                   help="run only these repeat indices, e.g. 0 (one time block per repeat)")
    e = sub.add_parser("extract")
    e.add_argument("root", type=Path)
    e.add_argument("out", type=Path)
    a = ap.parse_args(argv)

    if a.cmd == "plan":
        engines = a.engines.split(",")
        unknown = set(engines) - set(ENGINES)
        if unknown:
            raise SystemExit(f"unknown engines: {unknown}")
        slots = build_plan(load_queries(a.queries), engines, a.repeats,
                           a.qids.split(",") if a.qids else None)
        plan = {"protocol": "DAIV-LANG v001", "created": now(), "seed": SCHEDULE_SEED,
                "queries_file": str(a.queries), "queries_sha256": sha256_file(a.queries),
                "engines": engines, "repeats": a.repeats, "country": COUNTRY,
                "slots": slots}
        plan["plan_sha256"] = hashlib.sha256(
            json.dumps(slots, sort_keys=True).encode()).hexdigest()
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(plan, ensure_ascii=False, indent=1))
        print(f"{len(slots)} slots -> {a.out} (plan_sha256 {plan['plan_sha256'][:12]})")
    elif a.cmd == "run":
        workers = {k: int(v) for k, v in (x.split("=") for x in a.workers.split(","))}
        run(a.plan, a.root, a.max, a.sleep, workers=workers,
            engines=set(a.engines.split(",")) if a.engines else None,
            repeats={int(x) for x in a.repeat.split(",")} if a.repeat else None)
    else:
        extract(a.root, a.out)


if __name__ == "__main__":
    sys.exit(main())
