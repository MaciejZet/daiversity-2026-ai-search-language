"""DAIV-LANG amendment 02 analysis: location and access-path check, cross-day stability.
Run with data/cache/venv/bin/python. Exploratory, as declared in FREEZE.md (Poprawka 02).

usage:
  amend02.py MAIN_DERIVED AMEND_DERIVED OUT_DIR [--boot 10000]

Contrasts (same-day pairs come from the amendment run only):
  C1 location, ChatGPT direct API:   openai (country=PL)      vs openai-noloc
  C2 access path, ChatGPT:           openai-noloc (direct)    vs or-openai (OpenRouter)
  C3 location, Perplexity:           or-pplx (country=PL)     vs or-pplx-noloc
  T1 cross-day, Perplexity:          or-pplx main (day 1)     vs or-pplx amendment (day 3)
  T2 cross-day, ChatGPT:             or-openai main (day 1)   vs or-openai amendment (day 3)

For each contrast and each query language: per question, difference in mean Polish-source
share (A − B) and source overlap between conditions (J_between) against the noise floor
inside each condition (J_within, mean of A and B). Plus RQ1 (PL − EN) inside every
amendment condition, and the share of responses without citations.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

import numpy as np

import analyze as A

CONTRASTS = [
    ("C1_location_chatgpt", ("amend", "openai"), ("amend", "openai-noloc")),
    ("C2_path_chatgpt", ("amend", "openai-noloc"), ("amend", "or-openai")),
    ("C3_location_perplexity", ("amend", "or-pplx"), ("amend", "or-pplx-noloc")),
    ("T1_day_perplexity", ("main", "or-pplx"), ("amend", "or-pplx")),
    ("T2_day_chatgpt", ("main", "or-openai"), ("amend", "or-openai")),
]
LABEL = {"openai": "ChatGPT direct API, country=PL", "openai-noloc": "ChatGPT direct API, no location",
         "or-openai": "ChatGPT via OpenRouter, no location", "or-pplx": "Perplexity, country=PL",
         "or-pplx-noloc": "Perplexity, no location"}


def domain_lists(reps: dict) -> list[list[str]]:
    return [A.ordered_unique(c["domain"] for c in v["cites"]) for v in reps.values()]


def mean_share(reps: dict) -> float:
    vals = [A.pl_share(v["cites"]) for v in reps.values()]
    vals = [v for v in vals if not math.isnan(v)]
    return float(np.mean(vals)) if vals else math.nan


def within(lists) -> list[float]:
    return [A.jaccard(set(a), set(b)) for a, b in itertools.combinations(lists, 2)]


def nanmean(xs) -> float:
    xs = [x for x in xs if not math.isnan(x)]
    return float(np.mean(xs)) if xs else math.nan


def contrast(cells_a, cells_b, eng_a, eng_b, stratum, lang):
    out = {}
    for qid in sorted(stratum):
        ra, rb = cells_a.get((eng_a, qid, lang), {}), cells_b.get((eng_b, qid, lang), {})
        if not ra or not rb:
            continue
        la, lb = domain_lists(ra), domain_lists(rb)
        jw = nanmean(within(la) + within(lb))
        jb = nanmean([A.jaccard(set(a), set(b)) for a in la for b in lb])
        out[qid] = {"stratum": stratum[qid], "share_a": mean_share(ra), "share_b": mean_share(rb),
                    "j_within": jw, "j_between": jb}
        out[qid]["delta_share"] = out[qid]["share_a"] - out[qid]["share_b"]
        out[qid]["delta_overlap"] = jw - jb
    return out


def no_citation_share(cells, engine) -> dict:
    res = {}
    for lang in A.LANGS:
        for s in A.STRATA:
            reps = [v for (e, q, l), r in cells.items() if e == engine and l == lang
                    for v in r.values() if q[0] == s[0]]
            if reps:
                res[f"{lang}/{s}"] = sum(len(v["cites"]) == 0 for v in reps) / len(reps)
    return res


def run(main_derived: Path, amend_derived: Path, out: Path, n_boot: int) -> dict:
    data = {}
    for name, d in (("main", main_derived), ("amend", amend_derived)):
        cited, resp = A.load(d)
        data[name] = A.build(cited, resp)
    stratum = {**data["main"][1], **data["amend"][1]}
    g = A.rng()
    res = {"amendment": "02", "n_boot": n_boot, "contrasts": {}, "conditions": {}}
    for name, (sa, ea), (sb, eb) in CONTRASTS:
        ca, cb = data[sa][0], data[sb][0]
        if not any(k[0] == ea for k in ca) or not any(k[0] == eb for k in cb):
            continue
        res["contrasts"][name] = {"a": f"{sa}:{ea}", "b": f"{sb}:{eb}"}
        for lang in A.LANGS:
            pq = contrast(ca, cb, ea, eb, stratum, lang)
            res["contrasts"][name][lang] = {
                "delta_share": A.estimates(pq, "delta_share", n_boot, g),
                "j_within": A.estimates(pq, "j_within", n_boot, g)["ALL"],
                "j_between": A.estimates(pq, "j_between", n_boot, g)["ALL"],
                "delta_overlap": A.estimates(pq, "delta_overlap", n_boot, g),
                "per_question": pq,
            }
    cells_amend = data["amend"][0]
    for eng in sorted({k[0] for k in cells_amend}):
        pq = A.per_question(cells_amend, stratum, eng)
        res["conditions"][eng] = {"rq1": A.estimates(pq, "delta_pl", n_boot, g),
                                  "descriptives": A.descriptives(cells_amend, eng),
                                  "no_citations": no_citation_share(cells_amend, eng)}
    out.mkdir(parents=True, exist_ok=True)
    (out / "amend02-results.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    (out / "AMEND02-RESULTS.md").write_text(report(res))
    print(f"-> {out}/AMEND02-RESULTS.md")
    return res


def report(res: dict) -> str:
    L = ["# DAIV-LANG amendment 02: results (exploratory)", "",
         "Median over questions [95% bootstrap CI], Wilcoxon as a secondary check. Δ share = A − B, "
         "Δoverlap = J_within − J_between (> 0: conditions differ more than repeats do).", ""]
    for name, c in res["contrasts"].items():
        L += [f"## {name}: A = `{c['a']}`, B = `{c['b']}`", "",
              "| Query language | Stratum | Δ Polish share (A − B) | Δoverlap |", "|---|---|---|---|"]
        for lang in A.LANGS:
            for s in A.STRATA + ("ALL",):
                L.append(f"| {lang.upper()} | {s} | {A.fmt(c[lang]['delta_share'][s], pct=True)} | "
                         f"{A.fmt(c[lang]['delta_overlap'][s])} |")
        for lang in A.LANGS:
            jw, jb = c[lang]["j_within"], c[lang]["j_between"]
            if jw.get("median") is not None:
                L.append(f"\n{lang.upper()}: J_within {jw['median']:.2f}, J_between {jb['median']:.2f}.")
        L.append("")
    L += ["## RQ1 (PL − EN) in each amendment condition", "",
          "| Condition | Δ Polish share (ALL) | without citations (PL/GLOBAL, EN/GLOBAL) | responses |", "|---|---|---|---|"]
    for eng, c in res["conditions"].items():
        nc = c["no_citations"]
        L.append(f"| {LABEL.get(eng, eng)} | {A.fmt(c['rq1']['ALL'], pct=True)} | "
                 f"{nc.get('pl/GLOBAL', float('nan')):.0%}, {nc.get('en/GLOBAL', float('nan')):.0%} | "
                 f"{c['descriptives'].get('responses', 0)} |")
    return "\n".join(L) + "\n"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("main_derived", type=Path)
    ap.add_argument("amend_derived", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--boot", type=int, default=10_000)
    a = ap.parse_args(argv)
    run(a.main_derived, a.amend_derived, a.out, a.boot)


if __name__ == "__main__":
    main()
