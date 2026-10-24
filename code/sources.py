"""DAIV-LANG v001 source processing (protocol §5): URL normalization, one fetch per unique
URL, source language by content, Tranco rank.

Needs the isolated venv (trafilatura, fasttext-wheel, tldextract) and the fastText model:
  uv venv --python 3.12 data/cache/venv
  uv pip install --python data/cache/venv/bin/python trafilatura fasttext-wheel "numpy<2" tldextract
  curl -L -o data/cache/lid.176.ftz https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz

usage (run with data/cache/venv/bin/python):
  sources.py fetch CITATIONS.jsonl [...] PAGES.jsonl [--cache data/cache/pages] [--workers 8]
  sources.py enrich CITATIONS.jsonl [...] --pages PAGES.jsonl --tranco TRANCO.csv --out OUT_DIR
  sources.py qa-sample OUT_DIR/cited.jsonl QA.csv [--n 50]

fetch is resumable: each URL's record is cached in --cache and not refetched, except
fetch errors with --retry-errors.
Language chain (first that gives a confident label wins, method recorded):
  text  = fastText on trafilatura main text (>= 200 chars)
  html  = <html lang> attribute
  title = fastText on the citation title returned by the engine (>= 20 chars)
  unknown
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import random
import re
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request
import urllib.robotparser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

CODE = Path(__file__).resolve().parent
DEFAULT_MODEL = CODE.parent / "data/cache/lid.176.ftz"
SEED = "DAIVLANG-20261023"
UA = "Mozilla/5.0 (compatible; DAIV-LANG-research-fetcher/0.1)"
TIMEOUT_S = 20
MAX_BYTES = 3_000_000
HOST_DELAY_S = 1.0
MIN_TEXT = 200
MIN_TITLE = 20
MIN_PROB = 0.5

def _ssl_context() -> ssl.SSLContext:
    try:  # the uv-managed Python has no system CA bundle; certifi comes with trafilatura
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


SSL_CTX = _ssl_context()

TRACKING = re.compile(r"^(utm_.*|gclid|fbclid|msclkid|mc_cid|mc_eid|srsltid|_ga|_gl|"
                      r"cdc_aa_refval|ref_src|igshid|yclid)$", re.I)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------- normalization

_tld = None


def registered_domain(host: str) -> str:
    """eTLD+1 from the Public Suffix List snapshot bundled with tldextract (no network)."""
    global _tld
    if _tld is None:
        import tldextract
        _tld = tldextract.TLDExtract(suffix_list_urls=())
    ext = _tld(host)
    return (getattr(ext, "top_domain_under_public_suffix", None) or ext.registered_domain
            or host)


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").lower()
    if parts.port and parts.port not in (80, 443):
        host = f"{host}:{parts.port}"
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                       if not TRACKING.match(k)])
    return urlunsplit((parts.scheme.lower() or "https", host, parts.path or "/", query, ""))


# ---------------------------------------------------------------- language

class Detector:
    def __init__(self, model_path: Path = DEFAULT_MODEL):
        import fasttext
        self.model = fasttext.load_model(str(model_path))

    def __call__(self, text: str) -> tuple[str, float]:
        # Low-level call: fasttext's Python predict() uses np.array(copy=False), which fails
        # under NumPy 2 (pulled in by scipy). The trailing "\n" (end-of-sentence token) is
        # what predict() appends, so label and probability are identical to the wrapper.
        line = " ".join(text.split())[:5000] + "\n"
        (prob, label), = self.model.f.predict(line, 1, 0.0, "strict")
        return label.removeprefix("__label__"), float(prob)


def lang_class(code: str | None) -> str:
    if not code:
        return "unknown"
    code = code.lower().split("-")[0].split("_")[0]
    return code if code in ("pl", "en") else "other"


def decide_language(text: str | None, html_lang: str | None, title: str | None,
                    detect) -> dict:
    if text and len(text) >= MIN_TEXT:
        code, p = detect(text)
        if p >= MIN_PROB:
            return {"src_lang": lang_class(code), "src_lang_code": code,
                    "src_lang_prob": round(p, 4), "src_lang_method": "text"}
    if html_lang and lang_class(html_lang) != "unknown":
        return {"src_lang": lang_class(html_lang), "src_lang_code": html_lang.lower(),
                "src_lang_prob": None, "src_lang_method": "html"}
    if title and len(title) >= MIN_TITLE:
        code, p = detect(title)
        if p >= MIN_PROB:
            return {"src_lang": lang_class(code), "src_lang_code": code,
                    "src_lang_prob": round(p, 4), "src_lang_method": "title"}
    return {"src_lang": "unknown", "src_lang_code": None, "src_lang_prob": None,
            "src_lang_method": "none"}


# ---------------------------------------------------------------- fetch

HTML_LANG = re.compile(rb"<html[^>]*?\blang\s*=\s*[\"']?([A-Za-z]{2,3}(?:[-_][A-Za-z0-9]+)?)",
                       re.I | re.S)
META_CHARSET = re.compile(rb"<meta[^>]+charset\s*=\s*[\"']?([A-Za-z0-9_-]+)", re.I)


class Fetcher:
    def __init__(self):
        self.robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self.host_locks: dict[str, threading.Lock] = {}
        self.host_last: dict[str, float] = {}
        self.lock = threading.Lock()

    def _host_lock(self, host: str) -> threading.Lock:
        with self.lock:
            return self.host_locks.setdefault(host, threading.Lock())

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        base = f"{parts.scheme}://{parts.netloc}"
        with self.lock:
            known = base in self.robots
        if not known:
            rp = urllib.robotparser.RobotFileParser()
            try:
                req = urllib.request.Request(f"{base}/robots.txt", headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=TIMEOUT_S, context=SSL_CTX) as r:
                    rp.parse(r.read(500_000).decode("utf-8", "replace").splitlines())
            except Exception:
                rp = None  # unreachable or 4xx robots.txt: treated as allowed
            with self.lock:
                self.robots[base] = rp
        rp = self.robots[base]
        return rp is None or rp.can_fetch(UA, url)

    def get(self, url: str) -> dict:
        host = urlsplit(url).hostname or ""
        with self._host_lock(host):
            wait = self.host_last.get(host, 0) + HOST_DELAY_S - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.5",
                    "Accept-Language": "*"})
                with urllib.request.urlopen(req, timeout=TIMEOUT_S, context=SSL_CTX) as r:
                    body = r.read(MAX_BYTES + 1)
                    return {"http_status": r.status, "final_url": r.geturl(),
                            "content_type": r.headers.get("Content-Type", ""),
                            "charset": r.headers.get_content_charset(),
                            "body": body[:MAX_BYTES], "truncated": len(body) > MAX_BYTES}
            except urllib.error.HTTPError as e:
                return {"http_status": e.code, "error": f"HTTP {e.code}"}
            except Exception as e:
                return {"http_status": None, "error": f"{type(e).__name__}: {e}"[:300]}
            finally:
                self.host_last[host] = time.monotonic()


def decode(body: bytes, charset: str | None) -> str:
    if not charset:
        m = META_CHARSET.search(body[:4096])
        charset = m.group(1).decode() if m else "utf-8"
    try:
        return body.decode(charset, "replace")
    except LookupError:
        return body.decode("utf-8", "replace")


def process_url(url_norm: str, title: str | None, fetcher: Fetcher, detect,
                cache: Path, retry_errors: bool = False) -> dict:
    key = hashlib.sha1(url_norm.encode()).hexdigest()
    rec_path = cache / f"{key}.json"
    if rec_path.exists():
        rec = json.loads(rec_path.read_text())
        if not (retry_errors and rec.get("fetch_status") == "error"):
            return rec
    rec = {"url_norm": url_norm, "domain": registered_domain(urlsplit(url_norm).hostname or ""),
           "fetched": now(), "title_from_engine": title}
    text = html_lang = None
    if not fetcher.allowed(url_norm):
        rec["fetch_status"] = "robots_disallowed"
    else:
        r = fetcher.get(url_norm)
        rec.update({k: r.get(k) for k in ("http_status", "final_url", "content_type",
                                          "truncated", "error")})
        body = r.get("body")
        ctype = (r.get("content_type") or "").lower()
        if body is None:
            rec["fetch_status"] = "error"
        elif "html" not in ctype and not body.lstrip()[:15].lower().startswith((b"<!doctype", b"<html")):
            rec["fetch_status"] = "not_html"  # PDFs etc.: language from title only
        else:
            rec["fetch_status"] = "ok"
            m = HTML_LANG.search(body[:20000])
            html_lang = m.group(1).decode() if m else None
            import trafilatura
            text = trafilatura.extract(decode(body, r.get("charset")), include_comments=False,
                                       include_tables=False) or ""
            rec["html_lang"] = html_lang
            rec["text_chars"] = len(text)
            with gzip.open(cache / f"{key}.html.gz", "wb") as f:
                f.write(body)
    rec.update(decide_language(text, html_lang, title, detect))
    rec_path.write_text(json.dumps(rec, ensure_ascii=False))
    return rec


def read_citations(paths: list[Path]) -> list[dict]:
    rows = []
    for p in paths:
        rows += [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
    return rows


def fetch(citation_files: list[Path], out: Path, cache: Path, workers: int,
          fetcher: Fetcher | None = None, detect=None, retry_errors: bool = False) -> dict:
    cache.mkdir(parents=True, exist_ok=True)
    titles: dict[str, str | None] = {}
    for r in read_citations(citation_files):
        for c in r["citations"]:
            u = normalize_url(c["url"])
            if not titles.get(u):
                titles[u] = c.get("title")
    fetcher = fetcher or Fetcher()
    detect = detect or Detector()
    urls = sorted(titles)
    print(f"{len(urls)} unique URLs", flush=True)
    done = [0]
    lock = threading.Lock()

    def one(u):
        rec = process_url(u, titles[u], fetcher, detect, cache, retry_errors)
        with lock:
            done[0] += 1
            if done[0] % 25 == 0:
                print(f"{done[0]}/{len(urls)}", flush=True)
        return rec

    with ThreadPoolExecutor(workers) as ex:
        recs = list(ex.map(one, urls))
    with out.open("w", encoding="utf-8") as f:
        for rec in recs:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    summary = {"urls": len(recs)}
    for key in ("fetch_status", "src_lang", "src_lang_method"):
        counts: dict[str, int] = {}
        for rec in recs:
            counts[str(rec.get(key))] = counts.get(str(rec.get(key)), 0) + 1
        summary[key] = counts
    print(json.dumps(summary))
    return summary


# ---------------------------------------------------------------- enrich

def load_tranco(path: Path) -> dict[str, int]:
    ranks = {}
    with path.open() as f:
        for row in csv.reader(f):
            if len(row) >= 2 and row[0].isdigit():
                ranks.setdefault(row[1].strip().lower(), int(row[0]))
    return ranks


def tranco_bin(rank: int | None) -> str:
    if rank is None:
        return "unlisted"
    if rank <= 10_000:
        return "top10k"
    if rank <= 100_000:
        return "10k-100k"
    return "100k-1M"


def enrich(citation_files: list[Path], pages_path: Path, tranco_path: Path, out_dir: Path,
           detect=None) -> dict:
    pages = {}
    for line in pages_path.read_text().splitlines():
        rec = json.loads(line)
        pages[rec["url_norm"]] = rec
    ranks = load_tranco(tranco_path)
    detect = detect or Detector()
    out_dir.mkdir(parents=True, exist_ok=True)
    n_cited = n_resp = missing = 0
    with (out_dir / "cited.jsonl").open("w", encoding="utf-8") as fc, \
            (out_dir / "responses.jsonl").open("w", encoding="utf-8") as fr:
        for r in read_citations(citation_files):
            seen = set()
            for c in r["citations"]:
                u = normalize_url(c["url"])
                if u in seen:
                    continue
                seen.add(u)
                page = pages.get(u)
                if page is None:
                    missing += 1
                    page = {"domain": registered_domain(urlsplit(u).hostname or ""),
                            "src_lang": "unknown", "src_lang_method": "not_fetched"}
                rank = ranks.get(page["domain"])
                fc.write(json.dumps({
                    "slot_id": r["slot_id"], "qid": r["qid"], "stratum": r["stratum"],
                    "query_lang": r["lang"], "engine": r["engine"], "repeat": r["repeat"],
                    "rank_in_answer": len(seen) - 1, "url_norm": u, "domain": page["domain"],
                    "src_lang": page["src_lang"], "src_lang_method": page["src_lang_method"],
                    "src_lang_prob": page.get("src_lang_prob"),
                    "fetch_status": page.get("fetch_status"),
                    "tranco_rank": rank, "tranco_bin": tranco_bin(rank),
                }, ensure_ascii=False) + "\n")
                n_cited += 1
            text = r.get("answer_text") or ""
            code, p = detect(text) if text.strip() else (None, 0.0)
            fr.write(json.dumps({
                "slot_id": r["slot_id"], "qid": r["qid"], "stratum": r["stratum"],
                "query_lang": r["lang"], "engine": r["engine"], "repeat": r["repeat"],
                "model_returned": r.get("model_returned"), "n_cit": len(seen),
                "answer_lang": lang_class(code) if p >= MIN_PROB else "unknown",
                "answer_lang_prob": round(p, 4),
            }, ensure_ascii=False) + "\n")
            n_resp += 1
    summary = {"responses": n_resp, "citations": n_cited, "citations_not_fetched": missing,
               "tranco_entries": len(ranks)}
    print(json.dumps(summary))
    return summary


def qa_sample(cited_path: Path, out: Path, n: int) -> None:
    by_url = {}
    for line in cited_path.read_text().splitlines():
        r = json.loads(line)
        by_url.setdefault(r["url_norm"], r)
    urls = sorted(by_url)
    sample = random.Random(int(hashlib.sha256((SEED + "-QA").encode()).hexdigest(), 16)) \
        .sample(urls, min(n, len(urls)))
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["url_norm", "src_lang", "src_lang_method", "manual_lang", "note"])
        for u in sample:
            w.writerow([u, by_url[u]["src_lang"], by_url[u]["src_lang_method"], "", ""])
    print(f"{len(sample)} URLs -> {out} (fill manual_lang: pl/en/other/unknown)")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("paths", type=Path, nargs="+", help="CITATIONS.jsonl ... PAGES.jsonl")
    f.add_argument("--cache", type=Path, default=CODE.parent / "data/cache/pages")
    f.add_argument("--workers", type=int, default=8)
    f.add_argument("--retry-errors", action="store_true",
                   help="refetch URLs whose cached record is a fetch error")
    e = sub.add_parser("enrich")
    e.add_argument("citations", type=Path, nargs="+")
    e.add_argument("--pages", type=Path, required=True)
    e.add_argument("--tranco", type=Path, required=True)
    e.add_argument("--out", type=Path, required=True)
    q = sub.add_parser("qa-sample")
    q.add_argument("cited", type=Path)
    q.add_argument("out", type=Path)
    q.add_argument("--n", type=int, default=50)
    a = ap.parse_args(argv)
    if a.cmd == "fetch":
        *cites, out = a.paths
        if not cites:
            raise SystemExit("need at least one CITATIONS.jsonl and the PAGES.jsonl output")
        fetch(cites, out, a.cache, a.workers, retry_errors=a.retry_errors)
    elif a.cmd == "enrich":
        enrich(a.citations, a.pages, a.tranco, a.out)
    else:
        qa_sample(a.cited, a.out, a.n)


if __name__ == "__main__":
    sys.exit(main())
