"""Regenerate charts/fig5_motivation_dotplot (PNG + PDF).

Standalone reproduction of the fig5 motivation dotplot. Reads per-condition
macro-averaged accuracy from answers/{model}/{default,motivation}/_evaluation.json,
draws one row per model (Default open circle vs Motivation filled circle, connected
by a line coloured by the sign of the motivation effect), and labels each row with
the delta in percentage points.

Gemini 3.1 Flash Lite is excluded.
"""
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

ANSWERS = Path("answers")
CHARTS = Path("charts")

# Models to exclude from the figure.
EXCLUDE = set()

# answers/ directory name -> display label
MODEL_LABELS = {
    "harvard_us.anthropic.claude-sonnet-4-6": "Claude Sonnet 4.6",
    "harvard_mistral.mistral-large-3-675b-instruct": "Mistral Large 3",
    "harvard_us.anthropic.claude-opus-4-6-v1": "Claude Opus 4.6",
    "harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0": "Claude Haiku 4.5",
    "google_gemini-3.5-flash": "Gemini 3.5 Flash",
    "harvard_us.mistral.pixtral-large-2502-v1:0": "Pixtral Large",
    "openai_gpt-5.4-mini-2026-03-17": "GPT-5.4 Mini",
    "harvard_qwen.qwen3-vl-235b-a22b": "Qwen3-VL 235B",
    "google_gemini-3.1-pro-preview": "Gemini 3.1 Pro",
    "openai_gpt-5.5-2026-04-23": "GPT-5.5",
    "openai_gpt-5.4-nano-2026-03-17": "GPT-5.4 Nano",
    "google_gemini-3.1-flash-lite-preview": "Gemini 3.1 Flash Lite",
}

COLOR_HIGHER = "#0072B2"   # Okabe-Ito blue      — motivation improves accuracy
COLOR_LOWER  = "#D55E00"   # Okabe-Ito vermilion — motivation reduces accuracy
COLOR_DEFAULT_EDGE = "#333333"

mpl.rcParams.update({
    "font.family":       "serif",
    "font.size":         12,
    "axes.labelsize":    13,
    "xtick.labelsize":   11,
    "ytick.labelsize":   12,
    "legend.fontsize":   12,
    "axes.linewidth":    0.8,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "savefig.bbox":      "tight",
    "savefig.dpi":       600,
    "pdf.fonttype":      42,
    "ps.fonttype":       42,
})


def macro_score(model_dir: Path, condition: str):
    f = model_dir / condition / "_evaluation.json"
    if not f.exists():
        return None
    return json.loads(f.read_text())["summary"]["macro_averaged_score"] * 100.0


def load_rows():
    rows = []
    for model_dir in sorted(ANSWERS.iterdir()):
        if not model_dir.is_dir() or model_dir.name in EXCLUDE:
            continue
        if model_dir.name not in MODEL_LABELS:
            continue
        default = macro_score(model_dir, "default")
        motivation = macro_score(model_dir, "motivation")
        if default is None or motivation is None:
            continue
        rows.append({
            "label": MODEL_LABELS[model_dir.name],
            "default": default,
            "motivation": motivation,
            "diff": motivation - default,
        })
    # Largest positive delta at the top.
    rows.sort(key=lambda r: r["diff"])
    return rows


def fmt_delta(d: float) -> str:
    s = f"{d:+.1f}"
    return s.replace("-", "−")  # true minus sign


def main():
    rows = load_rows()
    n = len(rows)
    y = np.arange(n)

    fig, ax = plt.subplots(figsize=(8.5, 0.52 * n + 1.4))

    for i, r in enumerate(rows):
        color = COLOR_HIGHER if r["diff"] > 0 else COLOR_LOWER
        # connecting line
        ax.plot([r["default"], r["motivation"]], [y[i], y[i]],
                color=color, lw=2.0, zorder=1, solid_capstyle="round")
        # default: open circle
        ax.scatter(r["default"], y[i], s=55, facecolors="white",
                   edgecolors=COLOR_DEFAULT_EDGE, linewidths=1.3, zorder=3)
        # motivation: filled circle
        ax.scatter(r["motivation"], y[i], s=55, color=color, zorder=3)
        # delta label above the moved endpoint — glyph encodes direction redundantly
        glyph = "+" if r["diff"] > 0 else "−"
        delta_str = f"{glyph}{abs(r['diff']):.1f}"
        ax.text(r["motivation"], y[i] + 0.32, delta_str,
                color=color, ha="center", va="bottom", fontsize=11)

    ax.set_yticks(y)
    ax.set_yticklabels([r["label"] for r in rows])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Accuracy (%)")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", linestyle=":", color="#ccc", zorder=0)
    ax.set_axisbelow(True)

    # Legend
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], marker="o", linestyle="None", markersize=8,
               markerfacecolor="white", markeredgecolor=COLOR_DEFAULT_EDGE,
               markeredgewidth=1.3, label="Default"),
        Line2D([0], [0], marker="o", linestyle="None", markersize=8,
               color=COLOR_HIGHER, label="Motivation (higher)"),
        Line2D([0], [0], marker="o", linestyle="None", markersize=8,
               color=COLOR_LOWER, label="Motivation (lower)"),
    ]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 1.0),
              ncol=3, frameon=False, handletextpad=0.4, columnspacing=1.6)

    CHARTS.mkdir(exist_ok=True)
    fig.savefig(CHARTS / "fig5_motivation_dotplot.png")
    fig.savefig(CHARTS / "fig5_motivation_dotplot.pdf")
    plt.close(fig)

    print(f"Wrote fig5 with {n} models (excluded: {', '.join(sorted(EXCLUDE))})")
    for r in reversed(rows):
        print(f"  {r['label']:20} default={r['default']:5.1f}  "
              f"motivation={r['motivation']:5.1f}  diff={fmt_delta(r['diff'])}")


if __name__ == "__main__":
    main()
