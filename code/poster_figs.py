"""Poster figures for DAIV-LANG v001 from analysis/results.json (no new statistics).
Run with data/cache/venv/bin/python.

usage:
  poster_figs.py RESULTS.json OUT_DIR --fonts FONT_DIR [--width-px 1858]

FONT_DIR holds static TTFs named <prefix>-{Regular,Medium,SemiBold,Bold}.ttf (default prefix
IBMPlexSans; the A2 poster uses --font-prefix NunitoSans; both SIL OFL),
SIL OFL). Text is converted to outlines so the SVGs print with the poster's typeface.
Sizes are in CSS px at 96 px/in, so an SVG placed at --width-px is shown 1:1.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402
from matplotlib import font_manager as fm  # noqa: E402

STRATA = ("LOCAL", "GLOBAL", "CONSUMER")
T = {
    "en": {"LOCAL": "Poland-specific", "GLOBAL": "Global facts", "CONSUMER": "Consumer advice",
           "of": "{n} of 10 questions", "x_share": "Polish-language share of cited sources",
           "x_overlap": "shared cited domains between two answers (Jaccard)",
           "row": "{name}, asked in {lang}", "pl": "Polish", "en": "English",
           "x_tranco": "share of citations by popularity of the cited domain (Tranco rank)",
           "bins": ("top 10k", "10k–100k", "100k–1M", "not in top 1M"), "decimal": "."},
    "pl": {"LOCAL": "Sprawy polskie", "GLOBAL": "Wiedza ogólna", "CONSUMER": "Porady zakupowe",
           "of": "{n} z 10 pytań", "x_share": "udział źródeł polskojęzycznych",
           "x_overlap": "wspólne źródła w dwóch odpowiedziach",
           "row": "{name}, {lang}", "pl": "po polsku", "en": "po angielsku",
           "x_tranco": "udział cytowań według popularności domeny (ranking Tranco)",
           "bins": ("top 10 tys.", "10–100 tys.", "100 tys.–1 mln", "poza top 1 mln"),
           "decimal": ","},
}
L = T["en"]
ENGINES = (("or-pplx", "Perplexity", "sonar (API)"), ("or-openai", "OpenAI", "gpt-6-luna (API)"))
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, RULE = "#14171c", "#4a4f57", "#d9dce1"
SEQ = ("#0d366b", "#2a78d6", "#86b6ef", "#d5e5fa")
BIN_KEYS = ("top10k", "10k-100k", "100k-1M", "unlisted")
PX = 1 / 96  # inches per CSS px


def setup(font_dir: Path, prefix: str = "IBMPlexSans") -> None:
    for f in font_dir.glob(f"{prefix}-*.ttf"):
        fm.fontManager.addfont(str(f))
    family = fm.FontProperties(fname=str(font_dir / f"{prefix}-Regular.ttf")).get_name()
    plt.rcParams.update({
        "font.family": family, "svg.fonttype": "path", "text.color": INK,
        "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK,
        "axes.edgecolor": RULE, "font.size": 20,
    })


def save(fig, out: Path, stem: str) -> None:
    suffix = "" if L is T["en"] else f"_{[k for k, v in T.items() if v is L][0]}"
    fig.savefig(out / f"{stem}{suffix}.svg")
    fig.savefig(out / f"{stem}{suffix}.png", dpi=200)


def style(ax) -> None:
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(RULE)
    ax.tick_params(axis="y", length=0, labelsize=22, pad=18)
    ax.tick_params(axis="x", labelsize=19, color=RULE, length=8, pad=8)
    ax.grid(axis="x", color=RULE, linewidth=1.2)
    ax.set_axisbelow(True)


def title(ax, name, model) -> None:
    ax.text(0, 1.06, name, transform=ax.transAxes, fontsize=30, fontweight="bold", va="bottom")
    ax.text(1, 1.07, model, transform=ax.transAxes, fontsize=19, color=INK2, ha="right",
            va="bottom")


def ylabels(ax, pq, valid) -> None:
    labels = []
    for s in reversed(STRATA):
        n = sum(1 for q in pq.values() if q["stratum"] == s and valid(q))
        labels.append(f"{L[s]}\n{L['of'].format(n=n)}" if n < 10 else L[s])
    ax.set_yticks(range(len(STRATA)), labels)
    for t in ax.get_yticklabels():
        t.set_linespacing(1.3)


def fig_share(res: dict, out: Path, w_px: int, h_px: int) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(w_px * PX, h_px * PX))
    fig.subplots_adjust(left=0.15, right=0.975, top=0.82, bottom=0.255, wspace=0.38)
    for ax, (eng, name, model) in zip(axes, ENGINES):
        pq = res["engines"][eng]["per_question"]
        for i, s in enumerate(STRATA):
            qs = [q for q in pq.values() if q["stratum"] == s and not math.isnan(q["delta_pl"])]
            y0 = len(STRATA) - 1 - i
            for lang, dy, col in (("pl", 0.16, BLUE), ("en", -0.16, ORANGE)):
                vals = sorted(q[f"pl_share_{lang}"] for q in qs)
                ax.scatter(vals, [y0 + dy] * len(vals), s=150, color=col, alpha=0.30,
                           linewidths=0, zorder=2)
                if vals:
                    med = vals[len(vals) // 2] if len(vals) % 2 else \
                        (vals[len(vals) // 2 - 1] + vals[len(vals) // 2]) / 2
                    ax.scatter([med], [y0 + dy], s=560, color=col, edgecolors="white",
                               linewidths=3, zorder=3)
        ylabels(ax, pq, lambda q: not math.isnan(q["delta_pl"]))
        ax.set_xlim(-0.04, 1.04)
        ax.set_ylim(-0.6, 2.6)
        ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
        ax.set_xlabel(L["x_share"], fontsize=21, labelpad=14)
        style(ax)
        title(ax, name, model)
    save(fig, out, "poster_fig1_share")
    plt.close(fig)


def fig_overlap(res: dict, out: Path, w_px: int, h_px: int) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(w_px * PX, h_px * PX))
    fig.subplots_adjust(left=0.15, right=0.975, top=0.82, bottom=0.255, wspace=0.38)
    for ax, (eng, name, model) in zip(axes, ENGINES):
        pq = res["engines"][eng]["per_question"]

        def ok(q):
            return not (math.isnan(q["j_within"]) or math.isnan(q["j_cross"]))
        for i, s in enumerate(STRATA):
            qs = sorted((q for q in pq.values() if q["stratum"] == s and ok(q)),
                        key=lambda q: q["j_within"] - q["j_cross"])
            y0 = len(STRATA) - 1 - i
            for k, q in enumerate(qs):
                y = y0 + (k - (len(qs) - 1) / 2) * 0.075
                ax.plot([q["j_cross"], q["j_within"]], [y, y], color=RULE, linewidth=3,
                        zorder=1, solid_capstyle="round")
                ax.scatter([q["j_cross"]], [y], s=80, color=BLUE, zorder=2, linewidths=0)
                ax.scatter([q["j_within"]], [y], s=120, facecolors="white", edgecolors=INK,
                           linewidths=2.2, zorder=3)
        ylabels(ax, pq, ok)
        ax.set_xlim(-0.04, 1.04)
        ax.set_ylim(-0.6, 2.6)
        ax.set_xlabel(L["x_overlap"], fontsize=21, labelpad=14)
        ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
        style(ax)
        title(ax, name, model)
    save(fig, out, "poster_fig2_overlap")
    plt.close(fig)


def fig_tranco(res: dict, out: Path, w_px: int, h_px: int) -> None:
    fig, ax = plt.subplots(figsize=(w_px * PX, h_px * PX))
    fig.subplots_adjust(left=0.235, right=0.975, top=0.78, bottom=0.30)
    rows = []
    for eng, name, _ in ENGINES:
        for lang in ("pl", "en"):
            c = res["engines"][eng]["rq3_concentration"][f"{lang}/ALL"]["mean_bins"]
            rows.append((L["row"].format(name=name, lang=L[lang]), c))
    for y, (label, c) in enumerate(rows):
        left = 0.0
        for b, col in zip(BIN_KEYS, SEQ):
            w = c[b]
            ax.barh(y, w, left=left, color=col, height=0.66, edgecolor="white", linewidth=4)
            if w >= 0.07:
                ax.text(left + w / 2, y, f"{w:.0%}", ha="center", va="center", fontsize=22,
                        fontweight="semibold", color="white" if b in ("top10k", "10k-100k") else INK)
            left += w
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.set_xlabel(L["x_tranco"], fontsize=21, labelpad=14)
    style(ax)
    ax.grid(False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=col) for col in SEQ]
    ax.legend(handles, list(L["bins"]), frameon=False, ncol=4, fontsize=20,
              loc="lower left", bbox_to_anchor=(0, 1.04), borderaxespad=0, handlelength=1.4,
              columnspacing=2.2)
    save(fig, out, "poster_fig3_tranco")
    plt.close(fig)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("results", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--fonts", type=Path, required=True)
    ap.add_argument("--font-prefix", default="IBMPlexSans")
    ap.add_argument("--width-px", type=int, default=1858)
    ap.add_argument("--lang", choices=sorted(T), default="en")
    ap.add_argument("--heights", default="500,500,400", help="px heights of figs 1,2,3")
    a = ap.parse_args(argv)
    global L
    L = T[a.lang]
    setup(a.fonts, a.font_prefix)
    res = json.loads(a.results.read_text())
    a.out.mkdir(parents=True, exist_ok=True)
    h1, h2, h3 = (int(x) for x in a.heights.split(","))
    fig_share(res, a.out, a.width_px, h1)
    fig_overlap(res, a.out, a.width_px, h2)
    fig_tranco(res, a.out, a.width_px, h3)
    print(f"-> {a.out}")


if __name__ == "__main__":
    main()
