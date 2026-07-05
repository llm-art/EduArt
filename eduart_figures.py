"""Regenerate charts/fig1–fig4 with Okabe-Ito palette, cividis heatmap, 600 dpi.

Usage:
    python eduart_figures.py              # all four figures
    python eduart_figures.py --figs 2 3   # specific figures
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

# ─── Paths ────────────────────────────────────────────────────────────────────
ANSWERS = Path("answers")
CHARTS = Path("charts")

# ─── Okabe-Ito palette (all eight colors) ─────────────────────────────────────
OKABE = [
    "#000000",  # 0 Black
    "#E69F00",  # 1 Orange
    "#56B4E9",  # 2 Sky blue
    "#009E73",  # 3 Bluish green
    "#F0E442",  # 4 Yellow
    "#0072B2",  # 5 Blue
    "#D55E00",  # 6 Vermilion
    "#CC79A7",  # 7 Reddish purple
]

# Semantic aliases used for direction encoding in dotplots
INCREASE_COLOR = "#0072B2"   # Okabe blue      — condition improves score
DECREASE_COLOR = "#D55E00"   # Okabe vermilion — condition hurts score
DEFAULT_EDGE   = "#333333"   # near-black edge on open circles

mpl.rcParams.update({
    "font.family":       "serif",
    "font.size":         10,
    "axes.labelsize":    10,
    "axes.titlesize":    11,
    "legend.fontsize":   9,
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
    "axes.linewidth":    0.8,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "pdf.fonttype":      42,   # TrueType — embeds fonts properly
    "ps.fonttype":       42,
    "savefig.dpi":       600,
    "savefig.bbox":      "tight",
})

# ─── Question-type styling (color-blind safe, shape-redundant) ─────────────────
_QTYPE_DEFS = [
    # (internal key,           display label,      marker, Okabe color index)
    ("multiple_choice_radio", "MCQ radio",        "o", 1),  # orange
    ("multiple_choice_check", "MCQ check",        "s", 2),  # sky blue
    ("true_false",            "True/false",       "x", 3),  # bluish green
    ("positioning",           "Positioning",      "D", 4),  # yellow
    ("completion_closed",     "Completion (cl.)", "v", 5),  # blue
    ("completion_open",       "Completion (op.)", "^", 6),  # vermilion
    ("select_errors",         "Select errors",    "P", 7),  # reddish purple
]
TYPE_STYLE = {
    k: {"label": lbl, "marker": m, "color": OKABE[ci]}
    for k, lbl, m, ci in _QTYPE_DEFS
}
TYPE_ORDER = [t[0] for t in _QTYPE_DEFS]

# ─── Model display labels ──────────────────────────────────────────────────────
MODEL_LABELS = {
    "harvard_us.anthropic.claude-sonnet-4-6":              "Claude Sonnet 4.6",
    "harvard_mistral.mistral-large-3-675b-instruct":       "Mistral Large 3",
    "harvard_us.anthropic.claude-opus-4-6-v1":             "Claude Opus 4.6",
    "harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0": "Claude Haiku 4.5",
    "google_gemini-3.5-flash":                             "Gemini 3.5 Flash",
    "harvard_us.mistral.pixtral-large-2502-v1:0":          "Pixtral Large",
    "openai_gpt-5.4-mini-2026-03-17":                      "GPT-5.4 Mini",
    "harvard_qwen.qwen3-vl-235b-a22b":                     "Qwen3-VL 235B",
    "google_gemini-3.1-pro-preview":                       "Gemini 3.1 Pro",
    "openai_gpt-5.5-2026-04-23":                           "GPT-5.5",
    "openai_gpt-5.4-nano-2026-03-17":                      "GPT-5.4 Nano",
    "google_gemini-3.1-flash-lite-preview":                "Gemini 3.1 Flash Lite",
}


# ─── Helpers ───────────────────────────────────────────────────────────────────

def save(fig, stem: str) -> None:
    CHARTS.mkdir(exist_ok=True)
    fig.savefig(CHARTS / f"{stem}.png")
    fig.savefig(CHARTS / f"{stem}.pdf")
    plt.close(fig)
    print(f"  → charts/{stem}.{{png,pdf}}")


def load_model_dirs(condition: str = "default") -> list:
    """Return model dirs (in MODEL_LABELS) that have an _evaluation.json for condition."""
    return [
        d for d in sorted(ANSWERS.iterdir())
        if d.is_dir()
        and d.name in MODEL_LABELS
        and (d / condition / "_evaluation.json").exists()
    ]


def load_eval(model_dir: Path, condition: str) -> dict:
    return json.loads((model_dir / condition / "_evaluation.json").read_text())


def fmt_delta(d: float) -> str:
    """Format a signed delta, using true minus sign."""
    s = f"{d:+.1f}"
    return s.replace("-", "−")   # − (U+2212)


def _scatter_type(ax, xs, ys, style: dict, s: float = 18, alpha: float = 0.75):
    """Scatter for one question type; handles line-only markers (x) vs filled."""
    marker = style["marker"]
    color  = style["color"]
    if marker in ("x", "+"):
        ax.scatter(xs, ys, s=s * 1.3, marker=marker, color=color,
                   linewidths=1.2, zorder=2, alpha=alpha)
    elif color == OKABE[4]:              # yellow — needs dark edge to show on white
        ax.scatter(xs, ys, s=s, marker=marker, facecolors=color,
                   edgecolors="#888800", linewidths=0.6, zorder=2, alpha=alpha)
    else:
        ax.scatter(xs, ys, s=s, marker=marker, color=color,
                   edgecolors="none", zorder=2, alpha=alpha)


# ─────────────────────────────────────────────────────────────────────────────
# Fig 1 — Psychometric scatter (difficulty × discrimination)
# ─────────────────────────────────────────────────────────────────────────────

def fig1_psychometric() -> None:
    print("Fig 1: psychometric scatter …")

    model_dirs = load_model_dirs("default")

    # ── Build score matrix (models × questions) ───────────────────────────────
    # First pass: discover all question IDs and their types
    qid_type: dict[str, str] = {}
    for md in model_dirs:
        for item in load_eval(md, "default")["per_question"]:
            qid_type[item["question_id"]] = item["type"]
    all_qids = sorted(qid_type)
    qid_idx  = {q: i for i, q in enumerate(all_qids)}

    # Second pass: fill the matrix
    M = len(model_dirs)
    Q = len(all_qids)
    matrix = np.full((M, Q), np.nan)
    for mi, md in enumerate(model_dirs):
        for item in load_eval(md, "default")["per_question"]:
            matrix[mi, qid_idx[item["question_id"]]] = item["primary_score"]

    # ── Psychometric statistics ───────────────────────────────────────────────
    p    = np.nanmean(matrix, axis=0)          # difficulty
    total = np.nanmean(matrix, axis=1)         # model total score

    r_pb = np.full(Q, np.nan)
    for qi in range(Q):
        col   = matrix[:, qi]
        valid = ~np.isnan(col)
        if valid.sum() >= 3:
            r, _ = stats.pearsonr(col[valid], total[valid])
            r_pb[qi] = r

    # Group by question type
    by_type: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for qi, qid in enumerate(all_qids):
        if not (np.isnan(p[qi]) or np.isnan(r_pb[qi])):
            by_type[qid_type[qid]].append((p[qi], r_pb[qi]))

    # ── Plot ──────────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(2, 4, figsize=(13.0, 6.5),
                             sharex=True, sharey=True)
    panels = TYPE_ORDER + ["centroids"]
    centroids: dict[str, tuple[float, float]] = {}

    for idx, panel in enumerate(panels):
        ax = axes[idx // 4][idx % 4]

        if panel == "centroids":
            ax.set_title("Type centroids", fontsize=11)
            for t in TYPE_ORDER:
                if t not in centroids:
                    continue
                sty = TYPE_STYLE[t]
                cx, cy = centroids[t]
                _scatter_type(ax, [cx], [cy], sty, s=120, alpha=1.0)
        else:
            sty = TYPE_STYLE[panel]
            pts = by_type[panel]
            n   = len(pts)
            ax.set_title(f"{sty['label']} (n={n})", fontsize=11)
            if pts:
                xs, ys = zip(*pts)
                _scatter_type(ax, xs, ys, sty, s=18, alpha=0.72)
                centroids[panel] = (float(np.mean(xs)), float(np.mean(ys)))

        ax.axhline(0, color="#aaaaaa", lw=0.5, ls=":")
        ax.set_xlim(-0.04, 1.04)
        ax.set_ylim(-0.28, 1.05)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(length=3)
        if idx >= 4:
            ax.set_xlabel("Item difficulty ($p$)")
        if idx % 4 == 0:
            ax.set_ylabel("Discrimination ($r_{pb}$)")

    fig.tight_layout(pad=1.5)
    save(fig, "fig1_psychometric")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 2 — Accuracy heatmap (model × question type)
# ─────────────────────────────────────────────────────────────────────────────

def fig2_heatmap() -> None:
    print("Fig 2: accuracy heatmap …")

    col_labels = [TYPE_STYLE[t]["label"] for t in TYPE_ORDER]

    rows = []
    for md in load_model_dirs("default"):
        ev    = load_eval(md, "default")
        bt    = ev["summary"]["by_type"]
        macro = ev["summary"]["macro_averaged_score"] * 100
        row   = {"label": MODEL_LABELS[md.name], "macro": macro}
        for t in TYPE_ORDER:
            row[t] = bt[t]["mean"] * 100 if t in bt else np.nan
        rows.append(row)

    rows.sort(key=lambda r: r["macro"], reverse=True)
    row_labels = [r["label"] for r in rows]
    data = np.array([[r[t] for t in TYPE_ORDER] for r in rows])

    fig, ax = plt.subplots(figsize=(9.5, 0.52 * len(rows) + 1.4))

    im = ax.imshow(data, aspect="auto", cmap="cividis", vmin=0, vmax=100)

    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, rotation=30, ha="left", fontsize=9)
    ax.xaxis.set_ticks_position("top")
    ax.xaxis.set_label_position("top")
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=9)

    # Cell annotations — white text on dark cells, dark text on bright cells
    # cividis: low values are dark (→ white text), high values are bright (→ dark text)
    for i in range(len(rows)):
        for j, t in enumerate(TYPE_ORDER):
            v = data[i, j]
            if np.isnan(v):
                continue
            text_color = "white" if v < 55 else "#111111"
            ax.text(j, i, f"{v:.1f}", ha="center", va="center",
                    fontsize=8.5, color=text_color)

    # Grid lines between cells
    for x in np.arange(-0.5, len(col_labels), 1):
        ax.axvline(x, color="white", lw=0.4)
    for y in np.arange(-0.5, len(row_labels), 1):
        ax.axhline(y, color="white", lw=0.4)

    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("Accuracy (%)", fontsize=9)
    cbar.ax.tick_params(labelsize=8)

    ax.spines[:].set_visible(False)
    ax.tick_params(length=0)

    fig.tight_layout()
    save(fig, "fig2_heatmap")


# ─────────────────────────────────────────────────────────────────────────────
# Shared connected-dotplot helper
# ─────────────────────────────────────────────────────────────────────────────

def _dotplot(ax, rows: list[dict], *,
             sig_map: dict[str, str] | None = None,
             show_sig_note: bool = False) -> None:
    """
    Draw a connected dotplot.

    Each row dict: {label, base, end, diff}.
    sig_map: label → "* " | "† " | "" significance suffix.
    """
    if sig_map is None:
        sig_map = {}

    y = np.arange(len(rows))

    for i, r in enumerate(rows):
        color = INCREASE_COLOR if r["diff"] > 0 else DECREASE_COLOR
        glyph = "+"                  if r["diff"] > 0 else "−"  # + or −
        sig   = sig_map.get(r["label"], "")

        ax.plot([r["base"], r["end"]], [y[i], y[i]],
                color=color, lw=2.0, zorder=1, solid_capstyle="round")

        # Base marker: open circle
        ax.scatter(r["base"], y[i], s=55,
                   facecolors="white", edgecolors=DEFAULT_EDGE,
                   linewidths=1.3, zorder=3)

        # End marker: filled circle
        ax.scatter(r["end"], y[i], s=55, color=color, zorder=3)

        # Label above end marker: glyph + magnitude + significance
        delta_str = f"{glyph}{abs(r['diff']):.1f}"
        label_str = f"{delta_str} {sig}".rstrip() if sig else delta_str
        ax.text(r["end"], y[i] + 0.32, label_str,
                color=color, ha="center", va="bottom", fontsize=10)

    ax.set_yticks(y)
    ax.set_yticklabels([r["label"] for r in rows])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Accuracy (%)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", linestyle=":", color="#cccccc", zorder=0)
    ax.set_axisbelow(True)

    if show_sig_note:
        ax.text(0.01, -0.06, "* $p$ < 0.05   † $p$ < 0.10",
                transform=ax.transAxes, fontsize=8, color="#555555")


def _legend_dotplot(ax, base_label: str, higher_label: str, lower_label: str) -> None:
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], marker="o", linestyle="None", markersize=8,
               markerfacecolor="white", markeredgecolor=DEFAULT_EDGE,
               markeredgewidth=1.3, label=base_label),
        Line2D([0], [0], marker="o", linestyle="None", markersize=8,
               color=INCREASE_COLOR, label=higher_label),
        Line2D([0], [0], marker="o", linestyle="None", markersize=8,
               color=DECREASE_COLOR, label=lower_label),
    ]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 1.01),
              ncol=3, frameon=False, handletextpad=0.4, columnspacing=1.6)


# ─────────────────────────────────────────────────────────────────────────────
# Fig 3 — Motivation dotplot (all models, sorted most-negative first / top)
# ─────────────────────────────────────────────────────────────────────────────

def _wilcoxon_p(def_scores: dict, mot_scores: dict) -> float:
    """Paired Wilcoxon signed-rank p-value for per-question score changes."""
    common = set(def_scores) & set(mot_scores)
    diffs  = [mot_scores[q] - def_scores[q] for q in common]
    nonzero = [d for d in diffs if d != 0.0]
    if len(nonzero) < 5:
        return 1.0
    try:
        _, p = stats.wilcoxon(nonzero, alternative="two-sided")
        return float(p)
    except Exception:
        return 1.0


def fig3_motivation(exclude: set[str] | None = None,
                    sort_ascending: bool = False,
                    stem: str = "fig3_motivation") -> None:
    print(f"Fig 3 / {stem}: motivation dotplot …")

    if exclude is None:
        exclude = set()

    rows = []
    for md in load_model_dirs("default"):
        if md.name in exclude:
            continue
        if not (md / "motivation" / "_evaluation.json").exists():
            continue

        def_ev = load_eval(md, "default")
        mot_ev = load_eval(md, "motivation")

        def_score = def_ev["summary"]["macro_averaged_score"] * 100
        mot_score = mot_ev["summary"]["macro_averaged_score"] * 100

        def_pq = {item["question_id"]: item["primary_score"]
                  for item in def_ev["per_question"]}
        mot_pq = {item["question_id"]: item["primary_score"]
                  for item in mot_ev["per_question"]}
        pval = _wilcoxon_p(def_pq, mot_pq)

        rows.append({
            "label": MODEL_LABELS[md.name],
            "base":  def_score,
            "end":   mot_score,
            "diff":  mot_score - def_score,
            "pval":  pval,
        })

    rows.sort(key=lambda r: r["diff"], reverse=not sort_ascending)

    sig_map = {}
    for r in rows:
        p = r["pval"]
        sig_map[r["label"]] = ("*" if p < 0.05 else "†" if p < 0.10 else "")

    n   = len(rows)
    fig, ax = plt.subplots(figsize=(8.0, 0.52 * n + 1.6))

    _dotplot(ax, rows, sig_map=sig_map, show_sig_note=True)
    _legend_dotplot(ax, "Default", "Motivation (higher)", "Motivation (lower)")

    save(fig, stem)


# ─────────────────────────────────────────────────────────────────────────────
# Fig 4 — Image dotplot (no-image vs with-image)
# ─────────────────────────────────────────────────────────────────────────────

def fig4_image() -> None:
    print("Fig 4: image dotplot …")

    rows = []
    for md in load_model_dirs("default"):
        ev = load_eval(md, "default")
        pq = ev["per_question"]

        no_img   = [x["primary_score"] for x in pq if not x.get("has_image")]
        with_img = [x["primary_score"] for x in pq if     x.get("has_image")]

        if not no_img or not with_img:
            continue

        base = float(np.mean(no_img))  * 100
        end  = float(np.mean(with_img)) * 100

        rows.append({
            "label": MODEL_LABELS[md.name],
            "base":  base,
            "end":   end,
            "diff":  end - base,
        })

    rows.sort(key=lambda r: r["diff"], reverse=True)

    n   = len(rows)
    fig, ax = plt.subplots(figsize=(8.0, 0.52 * n + 1.6))

    _dotplot(ax, rows)
    _legend_dotplot(ax, "No image", "With image (higher)", "With image (lower)")

    save(fig, "fig4_image")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate EduArt figures 1–4")
    parser.add_argument("--figs", nargs="*", type=int, default=[1, 2, 3, 4],
                        metavar="N", help="Which figures to generate (default: 1 2 3 4)")
    args = parser.parse_args()

    fns = {
        1: fig1_psychometric,
        2: fig2_heatmap,
        3: lambda: fig3_motivation(exclude=set(), sort_ascending=False,
                                   stem="fig3_motivation"),
        4: fig4_image,
    }
    for n in args.figs:
        if n in fns:
            fns[n]()


if __name__ == "__main__":
    main()
