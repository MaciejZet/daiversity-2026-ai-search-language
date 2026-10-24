"""DAIV-LANG v001 analysis (protocol §6–7). Run with data/cache/venv/bin/python.

usage:
  analyze.py DERIVED_DIR OUT_DIR [--boot 10000] [--no-figures]

DERIVED_DIR holds cited.jsonl and responses.jsonl from sources.py enrich.
Writes OUT_DIR/results.json, OUT_DIR/RESULTS.md and poster figures (PNG + SVG).

Unit of inference is the question (n = 30, 10 per stratum); repeats are averaged.
Bootstrap: resample questions with replacement, within stratum for the pooled estimate.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

SEED = "DAIVLANG-20261023"
STRATA = ("LOCAL", "GLOBAL", "CONSUMER")
ENGINES = ("or-pplx", "or-openai")
ENGINE_LABEL = {"or-pplx": "Perplexity (sonar, API)", "or-openai": "OpenAI (gpt-6-luna, API)"}
LANGS = ("pl", "en")
NO_CITATION_FLAG = 0.20


def rng() -> np.random.Generator:
    return np.random.default_rng(int(hashlib.sha256(SEED.encode()).hexdigest(), 16) % 2**63)


def load(derived: Path):
    cited = [json.loads(x) for x in (derived / "cited.jsonl").read_text().splitlines() if x]
    resp = [json.loads(x) for x in (derived / "responses.jsonl").read_text().splitlines() if x]
    return cited, resp


# ---------------------------------------------------------------- per-response measures

def pl_share(cites: list[dict], unknown_in_denominator: bool = False,
             methods: set[str] | None = None) -> float:
    if methods is not None:
        cites = [c for c in cites if c["src_lang_method"] in methods]
    known = [c for c in cites if c["src_lang"] != "unknown"]
    denom = len(cites) if unknown_in_denominator else len(known)
    if denom == 0:
        return math.nan
    return sum(c["src_lang"] == "pl" for c in known) / denom


def ordered_unique(xs):
    seen, out = set(), []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def jaccard(a: set, b: set) -> float:
    return math.nan if not (a or b) else len(a & b) / len(a | b)


def rbo(a: list, b: list, p: float = 0.9) -> float:
    """Extrapolated rank-biased overlap (Webber et al. 2010, eq. 32) for uneven lists."""
    if not a and not b:
        return math.nan
    if not a or not b:
        return 0.0
    s, l_ = (a, b) if len(a) <= len(b) else (b, a)
    sn, ln = len(s), len(l_)
    x = [0] * (ln + 1)
    seen_s, seen_l = set(), set()
    for d in range(1, ln + 1):
        if d <= sn:
            seen_s.add(s[d - 1])
        seen_l.add(l_[d - 1])
        x[d] = len(seen_s & seen_l)
    total = sum(x[d] / d * p ** d for d in range(1, ln + 1))
    total += sum(x[sn] * (d - sn) / (sn * d) * p ** d for d in range(sn + 1, ln + 1))
    return (1 - p) / p * total + (x[ln] - x[sn]) / ln * p ** ln + x[sn] / sn * p ** ln


# ---------------------------------------------------------------- tables

def build(cited, resp):
    """cells[(engine, qid, lang)][repeat] = {"cites": [...], "n_cit": int}"""
    by_slot = defaultdict(list)
    for c in cited:
        by_slot[c["slot_id"]].append(c)
    cells = defaultdict(dict)
    stratum = {}
    for r in resp:
        cs = sorted(by_slot.get(r["slot_id"], []), key=lambda c: c["rank_in_answer"])
        cells[(r["engine"], r["qid"], r["query_lang"])][r["repeat"]] = {
            "cites": cs, "answer_lang": r["answer_lang"]}
        stratum[r["qid"]] = r["stratum"]
    return cells, stratum


def per_question(cells, stratum, engine, pl_kw=None, level="domain"):
    """Returns {qid: {...}} with mean pl_share per language, J/RBO within and cross."""
    pl_kw = pl_kw or {}
    key = "domain" if level == "domain" else "url_norm"
    out = {}
    for qid in sorted(stratum):
        reps = {lang: cells.get((engine, qid, lang), {}) for lang in LANGS}
        if not reps["pl"] or not reps["en"]:
            continue
        shares = {lang: np.nanmean([pl_share(v["cites"], **pl_kw) for v in reps[lang].values()]
                                   or [math.nan]) for lang in LANGS}
        lists = {lang: [ordered_unique(c[key] for c in v["cites"]) for v in reps[lang].values()]
                 for lang in LANGS}
        within_j, within_r = [], []
        for lang in LANGS:
            for a, b in itertools.combinations(lists[lang], 2):
                within_j.append(jaccard(set(a), set(b)))
                within_r.append(rbo(a, b))
        cross_j = [jaccard(set(a), set(b)) for a in lists["pl"] for b in lists["en"]]
        cross_r = [rbo(a, b) for a in lists["pl"] for b in lists["en"]]
        out[qid] = {
            "stratum": stratum[qid],
            "pl_share_pl": float(shares["pl"]), "pl_share_en": float(shares["en"]),
            "delta_pl": float(shares["pl"] - shares["en"]),
            "j_within": float(np.nanmean(within_j)) if within_j else math.nan,
            "j_cross": float(np.nanmean(cross_j)) if cross_j else math.nan,
            "rbo_within": float(np.nanmean(within_r)) if within_r else math.nan,
            "rbo_cross": float(np.nanmean(cross_r)) if cross_r else math.nan,
            "n_repeats": {lang: len(reps[lang]) for lang in LANGS},
        }
        out[qid]["delta_overlap"] = out[qid]["j_within"] - out[qid]["j_cross"]
        out[qid]["delta_rbo"] = out[qid]["rbo_within"] - out[qid]["rbo_cross"]
    return out


def summarize(values_by_stratum: dict[str, list[float]], n_boot: int, g) -> dict:
    """Median and 95% percentile bootstrap CI over questions; stratified when pooled."""
    vals = {s: np.array([v for v in vs if not math.isnan(v)]) for s, vs in values_by_stratum.items()}
    pooled = np.concatenate([v for v in vals.values()]) if vals else np.array([])
    if pooled.size == 0:
        return {"n": 0, "median": None, "ci95": [None, None], "wilcoxon_p": None}
    boots = np.empty(n_boot)
    for i in range(n_boot):
        boots[i] = np.median(np.concatenate(
            [v[g.integers(0, v.size, v.size)] for v in vals.values() if v.size]))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    nonzero = pooled[pooled != 0]
    p = float(wilcoxon(nonzero).pvalue) if nonzero.size >= 5 else None
    verdict = ("above zero" if lo > 0 else "below zero" if hi < 0
               else "no difference beyond noise shown")
    return {"n": int(pooled.size), "median": float(np.median(pooled)), "mean": float(pooled.mean()),
            "ci95": [float(lo), float(hi)], "wilcoxon_p": p, "verdict": verdict}


def estimates(pq: dict, field: str, n_boot: int, g) -> dict:
    res = {}
    for s in STRATA:
        res[s] = summarize({s: [q[field] for q in pq.values() if q["stratum"] == s]}, n_boot, g)
    res["ALL"] = summarize({s: [q[field] for q in pq.values() if q["stratum"] == s]
                            for s in STRATA}, n_boot, g)
    return res


def concentration(cells, stratum, engine):
    """RQ3, descriptive: per cell (qid × lang) pooled over repeats."""
    rows = []
    for (eng, qid, lang), reps in cells.items():
        if eng != engine:
            continue
        cites = [c for v in reps.values() for c in v["cites"]]
        if not cites:
            continue
        counts = defaultdict(int)
        for c in cites:
            counts[c["domain"]] += 1
        n = len(cites)
        rows.append({"qid": qid, "stratum": stratum[qid], "lang": lang,
                     "unique_domains": len(counts),
                     "hhi": sum((k / n) ** 2 for k in counts.values()),
                     "top10k_share": sum(c["tranco_bin"] == "top10k" for c in cites) / n,
                     "bins": {b: sum(c["tranco_bin"] == b for c in cites) / n
                              for b in ("top10k", "10k-100k", "100k-1M", "unlisted")}})
    out = {}
    for lang in LANGS:
        for s in STRATA + ("ALL",):
            rs = [r for r in rows if r["lang"] == lang and (s == "ALL" or r["stratum"] == s)]
            if not rs:
                continue
            out[f"{lang}/{s}"] = {
                "cells": len(rs),
                "median_unique_domains": float(np.median([r["unique_domains"] for r in rs])),
                "median_hhi": float(np.median([r["hhi"] for r in rs])),
                "median_top10k_share": float(np.median([r["top10k_share"] for r in rs])),
                "mean_bins": {b: float(np.mean([r["bins"][b] for r in rs]))
                              for b in ("top10k", "10k-100k", "100k-1M", "unlisted")}}
    return out


def descriptives(cells, engine):
    resps = [v for (eng, _, _), reps in cells.items() if eng == engine for v in reps.values()]
    if not resps:
        return {}
    n_cit = [len(v["cites"]) for v in resps]
    all_c = [c for v in resps for c in v["cites"]]
    methods = defaultdict(int)
    langs = defaultdict(int)
    for c in all_c:
        methods[c["src_lang_method"]] += 1
        langs[c["src_lang"]] += 1
    zero = sum(n == 0 for n in n_cit) / len(n_cit)
    mismatch = defaultdict(int)
    for (eng, _, lang), reps in cells.items():
        if eng == engine:
            for v in reps.values():
                mismatch[v["answer_lang"] == lang] += 1
    return {"responses": len(resps), "citations": len(all_c),
            "median_citations": float(np.median(n_cit)), "share_no_citations": zero,
            "flag_no_citations_over_20pct": zero > NO_CITATION_FLAG,
            "src_lang": dict(langs), "src_lang_method": dict(methods),
            "unknown_share": langs["unknown"] / len(all_c) if all_c else None,
            "answer_in_query_language": mismatch[True] / max(1, sum(mismatch.values()))}


# ---------------------------------------------------------------- figures

COLORS = {"pl": "#2a78d6", "en": "#eb6834"}
BIN_LABEL = {"top10k": "top 10k", "10k-100k": "10k–100k", "100k-1M": "100k–1M",
             "unlisted": "not in top 1M"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def _style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=10)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def figures(results: dict, per_q: dict, out: Path) -> list[str]:
    import matplotlib
    import matplotlib.ticker
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK,
                         "axes.labelcolor": INK2})
    written = []
    engines = [e for e in ENGINES if e in results["engines"]]

    # Fig 1: share of Polish-language sources, PL vs EN query, by stratum
    fig, axes = plt.subplots(1, len(engines), figsize=(5.2 * len(engines), 3.6), sharey=False,
                             squeeze=False)
    for ax, eng in zip(axes[0], engines):
        pq = per_q[eng]["main"]
        for i, s in enumerate(STRATA):
            qs = [q for q in pq.values() if q["stratum"] == s]
            for lang, dy in (("pl", 0.13), ("en", -0.13)):
                vals = [q[f"pl_share_{lang}"] for q in qs if not math.isnan(q[f"pl_share_{lang}"])]
                y = len(STRATA) - 1 - i + dy
                ax.scatter(vals, [y] * len(vals), s=22, color=COLORS[lang], alpha=0.35,
                           linewidths=0, zorder=2)
                if vals:
                    ax.scatter([np.median(vals)], [y], s=90, color=COLORS[lang], zorder=3,
                               edgecolors="white", linewidths=2,
                               label=f"{lang.upper()} query" if i == 0 else None)
        ns = {s: sum(1 for q in pq.values() if q["stratum"] == s
                     and not math.isnan(q["delta_pl"])) for s in STRATA}
        ax.set_yticks(range(len(STRATA)), [f"{s.lower()}\n(n={ns[s]})" for s in reversed(STRATA)])
        ax.set_xlim(-0.03, 1.03)
        ax.set_ylim(-0.5, len(STRATA) - 0.5)
        ax.set_xlabel("share of Polish-language sources")
        ax.set_title(ENGINE_LABEL[eng], fontsize=12, loc="left", color=INK)
        _style(ax)
    fig.legend(*axes[0][0].get_legend_handles_labels(), frameon=False, ncol=2, fontsize=9,
               loc="upper right")
    fig.text(0.01, 0.01, "small dots: questions (mean of repeats); large dot: median; "
             "n = questions with citations in both languages",
             fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    for ext in ("png", "svg"):
        fig.savefig(out / f"fig1_pl_share.{ext}", dpi=300)
    plt.close(fig)
    written.append("fig1_pl_share")

    # Fig 2: noise floor vs cross-language overlap (domain Jaccard), paired per question
    fig, axes = plt.subplots(1, len(engines), figsize=(5.2 * len(engines), 3.6), sharey=False,
                             squeeze=False)
    for ax, eng in zip(axes[0], engines):
        pq = per_q[eng]["main"]
        for i, s in enumerate(STRATA):
            qs = [q for q in pq.values() if q["stratum"] == s
                  and not (math.isnan(q["j_within"]) or math.isnan(q["j_cross"]))]
            y0 = len(STRATA) - 1 - i
            for k, q in enumerate(qs):
                y = y0 + (k - (len(qs) - 1) / 2) * 0.06
                ax.plot([q["j_cross"], q["j_within"]], [y, y], color=GRID, linewidth=1.5, zorder=1)
                ax.scatter([q["j_cross"]], [y], s=18, color=COLORS["pl"], zorder=2,
                           label="PL vs EN query" if (i, k) == (0, 0) else None)
                ax.scatter([q["j_within"]], [y], s=46, facecolors="none", edgecolors=INK2,
                           linewidths=1.4, zorder=3,
                           label="same language (noise floor)" if (i, k) == (0, 0) else None)
        ns = {s: sum(1 for q in pq.values() if q["stratum"] == s
                     and not (math.isnan(q["j_within"]) or math.isnan(q["j_cross"])))
              for s in STRATA}
        ax.set_yticks(range(len(STRATA)), [f"{s.lower()}\n(n={ns[s]})" for s in reversed(STRATA)])
        ax.set_xlim(-0.03, 1.03)
        ax.set_ylim(-0.5, len(STRATA) - 0.5)
        ax.set_xlabel("overlap of cited domains (Jaccard)")
        ax.set_title(ENGINE_LABEL[eng], fontsize=12, loc="left", color=INK)
        _style(ax)
    fig.legend(*axes[0][0].get_legend_handles_labels(), frameon=False, ncol=2, fontsize=9,
               loc="upper right")
    fig.text(0.01, 0.01, "one line per question; the further the ring from the dot, "
             "the more the query language changes the sources", fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    for ext in ("png", "svg"):
        fig.savefig(out / f"fig2_overlap.{ext}", dpi=300)
    plt.close(fig)
    written.append("fig2_overlap")

    # Fig 3: popularity of cited domains (Tranco bins), sequential single hue
    bins = ("top10k", "10k-100k", "100k-1M", "unlisted")
    seq = ("#0d366b", "#2a78d6", "#86b6ef", "#d5e5fa")  # one hue, dark -> light
    fig, ax = plt.subplots(figsize=(7.5, 2.8))
    labels, y = [], 0
    for eng in engines:
        for lang in LANGS:
            c = results["engines"][eng]["rq3_concentration"].get(f"{lang}/ALL")
            if not c:
                continue
            left = 0.0
            for b, col in zip(bins, seq):
                w = c["mean_bins"][b]
                ax.barh(y, w, left=left, color=col, height=0.62, edgecolor="white", linewidth=2,
                        label=BIN_LABEL[b] if y == 0 else None)
                if w >= 0.08:
                    ax.text(left + w / 2, y, f"{w:.0%}", ha="center", va="center", fontsize=8,
                            color="white" if b in ("top10k", "10k-100k") else INK)
                left += w
            labels.append(f"{ENGINE_LABEL[eng].split(' ')[0]}, {lang.upper()} query")
            y += 1
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("share of citations by Tranco rank of the cited domain")
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.legend(frameon=False, ncol=4, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.32))
    _style(ax)
    ax.grid(False)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(out / f"fig3_tranco.{ext}", dpi=300)
    plt.close(fig)
    written.append("fig3_tranco")
    return written


# ---------------------------------------------------------------- report

def fmt(e: dict, pct: bool = False) -> str:
    if not e or e.get("median") is None:
        return "—"
    f = (lambda v: f"{v * 100:+.0f} pp") if pct else (lambda v: f"{v:+.2f}")
    p = e["wilcoxon_p"]
    return (f"{f(e['median'])} [{f(e['ci95'][0])}; {f(e['ci95'][1])}], n={e['n']}"
            + (f", p={p:.3g}" if p is not None else ""))


def report(results: dict) -> str:
    lines = ["# DAIV-LANG v001: results", "",
             f"Data: `{results['input']}`. Bootstrap {results['n_boot']} resamples, seed `{SEED}`. "
             "Median over questions [95% CI], Wilcoxon test as a secondary check. "
             "Verdict per protocol §7: CI entirely above zero = effect; otherwise \"not shown\".", ""]
    for eng, r in results["engines"].items():
        d = r["descriptives"]
        lines += [f"## {ENGINE_LABEL.get(eng, eng)}", "",
                  f"Responses {d['responses']}, citations {d['citations']}, median citations "
                  f"{d['median_citations']:.0f}, without citations {d['share_no_citations']:.0%}"
                  + (" **(> 20%, §7 flag)**" if d["flag_no_citations_over_20pct"] else "")
                  + f", source language unknown {d['unknown_share']:.0%}, answer in the query language "
                  f"{d['answer_in_query_language']:.0%}.", "",
                  "| Stratum | RQ1 Δ Polish share (PL − EN) | RQ2 Δoverlap (J_within − J_cross) | Δ RBO |",
                  "|---|---|---|---|"]
        for s in STRATA + ("ALL",):
            lines.append(f"| {s} | {fmt(r['rq1'][s], pct=True)} | {fmt(r['rq2'][s])} | "
                         f"{fmt(r['rq2_rbo'][s])} |")
        lines += ["", "Verdicts (ALL): RQ1 " + r["rq1"]["ALL"].get("verdict", "—")
                  + "; RQ2 " + r["rq2"]["ALL"].get("verdict", "—") + ".", "",
                  "**Sensitivity analyses (ALL):**", ""]
        for name, s in r["sensitivity"].items():
            lines.append(f"- {name}: {fmt(s, pct=name.startswith('rq1'))}")
        lines += ["", "**RQ3 (descriptive; cells = question × language, pooled over repeats):**", "",
                  "| Language/stratum | median unique domains | median HHI | median top-10k share |",
                  "|---|---|---|---|"]
        for k, c in r["rq3_concentration"].items():
            lines.append(f"| {k} | {c['median_unique_domains']:.0f} | {c['median_hhi']:.3f} | "
                         f"{c['median_top10k_share']:.0%} |")
        lines.append("")
    lines += ["Engines are not compared in absolute numbers: OpenAI returns inline citations, "
              "Perplexity a list of search results (PROTOCOL.md, smoke run).", ""]
    return "\n".join(lines)


def analyze(derived: Path, out: Path, n_boot: int = 10_000, make_figures: bool = True) -> dict:
    cited, resp = load(derived)
    cells, stratum = build(cited, resp)
    out.mkdir(parents=True, exist_ok=True)
    g = rng()
    results = {"protocol": "DAIV-LANG v001", "input": str(derived), "n_boot": n_boot,
               "engines": {}}
    per_q = {}
    for eng in ENGINES:
        if not any(k[0] == eng for k in cells):
            continue
        pq = per_question(cells, stratum, eng)
        sens_q = {
            "rq1_unknown_in_denominator": per_question(cells, stratum, eng,
                                                       {"unknown_in_denominator": True}),
            "rq1_only_text_html_methods": per_question(cells, stratum, eng,
                                                       {"methods": {"text", "html"}}),
            "rq2_url_level": per_question(cells, stratum, eng, level="url"),
        }
        no_local = {k: v for k, v in pq.items() if v["stratum"] != "LOCAL"}
        sens = {
            "rq1_unknown_in_denominator": estimates(sens_q["rq1_unknown_in_denominator"],
                                                    "delta_pl", n_boot, g)["ALL"],
            "rq1_only_text_html_methods": estimates(sens_q["rq1_only_text_html_methods"],
                                                    "delta_pl", n_boot, g)["ALL"],
            "rq1_without_LOCAL": estimates(no_local, "delta_pl", n_boot, g)["ALL"],
            "rq2_url_level": estimates(sens_q["rq2_url_level"], "delta_overlap", n_boot, g)["ALL"],
            "rq2_without_LOCAL": estimates(no_local, "delta_overlap", n_boot, g)["ALL"],
        }
        results["engines"][eng] = {
            "descriptives": descriptives(cells, eng),
            "rq1": estimates(pq, "delta_pl", n_boot, g),
            "rq2": estimates(pq, "delta_overlap", n_boot, g),
            "rq2_rbo": estimates(pq, "delta_rbo", n_boot, g),
            "rq2_levels": {k: estimates(pq, k, n_boot, g)["ALL"] for k in ("j_within", "j_cross")},
            "sensitivity": sens,
            "rq3_concentration": concentration(cells, stratum, eng),
            "per_question": pq,
        }
        per_q[eng] = {"main": pq}
    (out / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1))
    (out / "RESULTS.md").write_text(report(results))
    if make_figures and results["engines"]:
        results["figures"] = figures(results, per_q, out)
    print(f"-> {out}/RESULTS.md, results.json" + (", figures" if make_figures else ""))
    return results


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("derived", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--boot", type=int, default=10_000)
    ap.add_argument("--no-figures", action="store_true")
    a = ap.parse_args(argv)
    analyze(a.derived, a.out, a.boot, not a.no_figures)


if __name__ == "__main__":
    main()
