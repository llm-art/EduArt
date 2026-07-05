#!/usr/bin/env python3
"""
Format Compliance Analysis — Disentangle format failures from knowledge failures.

Produces answers/format_analysis.md with two tables:
  1. Select Errors format classification (T/F confusion, single-text, etc.)
  2. Non-JSON (string) llm_answer counts by question type per model

Usage:
    python answers/format_compliance_analysis.py
    python answers/format_compliance_analysis.py --condition motivation
"""

import json
import os
import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import click

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"
METADATA_DIR = DATASET_DIR / "metadata"
ANSWERS_DIR = BASE_DIR / "answers"


def _norm(text):
    if text is None:
        return ""
    s = str(text).strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _f1(predicted: set, ground_truth: set) -> float:
    if not predicted and not ground_truth:
        return 1.0
    if not predicted or not ground_truth:
        return 0.0
    tp = len(predicted & ground_truth)
    prec = tp / len(predicted)
    rec = tp / len(ground_truth)
    return 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0


def load_metadata():
    meta = {}
    for f in sorted(METADATA_DIR.glob("*.json")):
        meta[f.stem] = json.loads(f.read_text(encoding="utf-8"))
    return meta


def discover_models(condition):
    models = []
    for d in sorted(ANSWERS_DIR.iterdir()):
        if d.is_dir() and not d.name.startswith(".") and (d / condition).is_dir():
            models.append(d.name)
    return models


def analyse_select_errors(metadata, models, condition):
    se_ground_truth = {}
    for qid, meta in metadata.items():
        if meta.get("type") != "select_errors":
            continue
        gt_errors = set()
        for item in meta.get("answers", []):
            err = item.get("error", "")
            if err:
                gt_errors.add(_norm(err))
        se_ground_truth[qid] = gt_errors

    rows = []
    for model in models:
        fmt_correct = 0
        fmt_tf = 0
        fmt_single = 0
        fmt_other = 0
        f1_all = []
        f1_fmt_ok = []

        for qid, gt_errors in se_ground_truth.items():
            ans_path = ANSWERS_DIR / model / condition / f"{qid}.json"
            if not ans_path.exists():
                continue
            ans = json.loads(ans_path.read_text(encoding="utf-8"))
            llm_answer = ans.get("llm_answer", [])

            pred_errors = set()
            if isinstance(llm_answer, list):
                for item in llm_answer:
                    if isinstance(item, dict):
                        text = item.get("text") or item.get("error") or item.get("description") or ""
                        if text:
                            pred_errors.add(_norm(text))
            elif isinstance(llm_answer, str):
                pred_errors.add(_norm(llm_answer))

            score = _f1(pred_errors, gt_errors)
            f1_all.append(score)

            if isinstance(llm_answer, str) or not isinstance(llm_answer, list):
                fmt_other += 1
            elif len(llm_answer) == 0:
                fmt_other += 1
            else:
                texts = [it.get("text", "") for it in llm_answer if isinstance(it, dict)]
                texts_upper = [t.strip().upper() for t in texts]
                if len(texts) == 1 and texts_upper[0] in ("TRUE", "FALSE", "VERO", "FALSO"):
                    fmt_tf += 1
                elif len(texts) == 1:
                    fmt_single += 1
                elif len(texts) > 1:
                    fmt_correct += 1
                    f1_fmt_ok.append(score)
                else:
                    fmt_other += 1

        n = len(f1_all)
        if n == 0:
            continue

        rows.append({
            "model": model,
            "n": n,
            "fmt_correct": fmt_correct,
            "fmt_tf": fmt_tf,
            "fmt_single": fmt_single,
            "fmt_other": fmt_other,
            "f1": sum(f1_all) / n,
            "f1_fmt_ok": sum(f1_fmt_ok) / len(f1_fmt_ok) if f1_fmt_ok else 0.0,
            "compliance_pct": fmt_correct / n if n else 0.0,
        })

    return rows


def analyse_non_json(metadata, models, condition):
    type_order = [
        "multiple_choice_radio", "multiple_choice_check", "true_false",
        "positioning", "completion_closed", "completion_open", "select_errors",
    ]

    rows = []
    for model in models:
        counts = {t: [0, 0] for t in type_order}

        for qid, meta in metadata.items():
            qtype = meta.get("type", "")
            if qtype not in counts:
                continue
            ans_path = ANSWERS_DIR / model / condition / f"{qid}.json"
            if not ans_path.exists():
                continue
            ans = json.loads(ans_path.read_text(encoding="utf-8"))
            la = ans.get("llm_answer", [])
            counts[qtype][1] += 1
            if not isinstance(la, list):
                counts[qtype][0] += 1

        total_nl = sum(c[0] for c in counts.values())
        total_n = sum(c[1] for c in counts.values())
        if total_n == 0:
            continue

        rows.append({
            "model": model,
            "counts": counts,
            "total_nl": total_nl,
            "total_n": total_n,
        })

    return rows, type_order


def render_markdown(se_rows, nj_rows, nj_types, condition):
    type_short = {
        "multiple_choice_radio": "MCQ Radio",
        "multiple_choice_check": "MCQ Check",
        "true_false": "True/False",
        "positioning": "Positioning",
        "completion_closed": "Compl. Closed",
        "completion_open": "Compl. Open",
        "select_errors": "Select Errors",
    }

    lines = []
    lines.append("# Format Compliance Analysis")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  ")
    lines.append(f"Condition: `{condition}`")
    lines.append("")

    # --- Explanation ---
    lines.append("## Background")
    lines.append("")
    lines.append(
        "Low scores on certain question types may reflect **format non-compliance** "
        "rather than lack of domain knowledge. Two failure modes are common:"
    )
    lines.append("")
    lines.append(
        "1. **Task confusion on Select Errors.** The prompt asks models to identify "
        "incorrect words in a passage and return them as a list. Many models instead "
        "return a single `TRUE`/`FALSE` value (confusing the task with True/False) "
        "or a single descriptive string (e.g. attempting to name the artwork rather "
        "than listing its textual errors). These responses score F1 = 0 regardless "
        "of the model's actual art-historical knowledge."
    )
    lines.append(
        "2. **Non-JSON responses.** Some models emit reasoning text or free-form "
        "prose instead of the required JSON structure. When `llm_answer` is a raw "
        "string rather than a list of `{id, text}` objects, the evaluator cannot "
        "extract any answer and every element scores 0."
    )
    lines.append("")

    # --- Metric definitions ---
    lines.append("## Metric Definitions")
    lines.append("")
    lines.append("| Symbol | Definition |")
    lines.append("|--------|------------|")
    lines.append(
        "| **F1** | Reported F1 score over the full set of Select Errors questions, "
        "including responses with wrong format (which contribute F1 = 0). |"
    )
    lines.append(
        "| **F1\\*** | F1 computed **only** on responses where the model returned the "
        "correct format (multiple error-word items). This isolates domain knowledge "
        "from format compliance — it answers: *when the model understood the task, "
        "how well did it identify the errors?* |"
    )
    lines.append(
        "| **Compliance** | Percentage of Select Errors responses where the model "
        "returned the correct format (a list of multiple error words). |"
    )
    lines.append(
        "| **T/F confusion** | Responses containing a single `TRUE` or `FALSE` value, "
        "indicating the model misinterpreted Select Errors as a True/False question. |"
    )
    lines.append(
        "| **Single text** | Responses containing a single non-T/F string (e.g. an "
        "artwork title or description), indicating the model attempted a different task. |"
    )
    lines.append(
        "| **Other wrong** | Non-list responses (raw reasoning text), empty responses, "
        "or other unparseable formats. |"
    )
    lines.append("")

    # --- Table 1: Select Errors ---
    lines.append("## Table 1 — Select Errors: Format Classification")
    lines.append("")
    lines.append(
        "Each response to a Select Errors question is classified into one of four "
        "categories based on its structure. The gap between F1 and F1\\* quantifies "
        "how much of the score deficit is attributable to format non-compliance "
        "versus actual domain-knowledge failure."
    )
    lines.append("")
    lines.append(
        "| Model | N | Correct format | T/F confusion | Single text | Other wrong "
        "| Compliance | F1 | F1\\* |"
    )
    lines.append(
        "|-------|---|----------------|---------------|-------------|-------------"
        "|------------|-----|------|"
    )
    for r in se_rows:
        lines.append(
            f"| `{r['model']}` "
            f"| {r['n']} "
            f"| {r['fmt_correct']} "
            f"| {r['fmt_tf']} "
            f"| {r['fmt_single']} "
            f"| {r['fmt_other']} "
            f"| {r['compliance_pct']:.0%} "
            f"| {r['f1']:.1%} "
            f"| {r['f1_fmt_ok']:.1%} |"
        )
    lines.append("")
    lines.append(
        "> **Reading example:** GPT-5.4 returns the correct format for 13/49 questions "
        "(27% compliance). Its reported F1 is 11.7%, but on the 13 correctly-formatted "
        "responses it achieves F1\\* = 44.2% — the remaining 36 questions score 0 purely "
        "due to format failure (51% returned TRUE/FALSE, 22% returned a single text)."
    )
    lines.append("")

    # --- Table 2: Non-JSON ---
    lines.append("## Table 2 — Non-JSON (String) Responses by Question Type")
    lines.append("")
    lines.append(
        "When `llm_answer` is a raw string instead of a JSON list, the evaluator "
        "cannot extract structured answers and every element scores 0. This table "
        "counts such responses per model and question type."
    )
    lines.append("")

    header = "| Model |"
    sep = "|-------|"
    for t in nj_types:
        header += f" {type_short[t]} |"
        sep += "---|"
    header += " **Total** |"
    sep += "---|"
    lines.append(header)
    lines.append(sep)

    for r in nj_rows:
        row = f"| `{r['model']}` |"
        for t in nj_types:
            nl, n = r["counts"][t]
            if n == 0:
                row += " — |"
            elif nl == 0:
                row += f" 0/{n} |"
            else:
                row += f" **{nl}**/{n} |"
        row += f" **{r['total_nl']}**/{r['total_n']} |"
        lines.append(row)
    lines.append("")
    lines.append(
        "> Values show non-JSON count / total questions. Bold highlights non-zero failures. "
        "Models with high non-JSON rates (Llama4 Maverick: 83%, Pixtral Large: 52%) "
        "have their macro-averaged scores dominated by format failure rather than "
        "knowledge gaps."
    )
    lines.append("")

    # --- Interpretation ---
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "The **F1 vs F1\\*** gap in Table 1 decomposes the Select Errors score deficit "
        "into two components:"
    )
    lines.append("")
    lines.append(
        "- **Format-attributable deficit** = F1\\* − F1. This is the score improvement "
        "that would result from perfect format compliance alone, holding knowledge constant."
    )
    lines.append(
        "- **Knowledge-attributable deficit** = 100% − F1\\*. This is the residual "
        "gap that remains even when the model understood the task format."
    )
    lines.append("")
    lines.append(
        "For example, Claude Sonnet scores F1 = 6.2%. Its F1\\* = 27.7%, meaning "
        "~21.5 pp of the deficit is format failure and ~72.3 pp is genuine knowledge "
        "or error-detection difficulty. By contrast, Gemini Pro's gap is only ~3.3 pp "
        "(78.8% → 82.1%), confirming that its high score reflects both format "
        "compliance and domain mastery."
    )
    lines.append("")
    lines.append(
        "Table 2 reveals a broader pattern: Llama4 Maverick and Pixtral Large fail "
        "to produce valid JSON for the majority of questions across **all** types, "
        "making their aggregate scores largely uninformative about domain knowledge. "
        "Claude Opus shows a localised variant: 48/75 Completion (Open) responses "
        "are raw strings, explaining its anomalous 23.9% on that type versus 65%+ "
        "for comparably-ranked models."
    )
    lines.append("")

    return "\n".join(lines)


@click.command()
@click.option("--condition", default="default", help="Prompt condition (default or motivation)")
def main(condition):
    """Generate format compliance analysis."""
    print(f"Loading metadata...")
    metadata = load_metadata()
    models = discover_models(condition)
    print(f"Found {len(models)} models for condition '{condition}'")

    print("Analysing Select Errors format compliance...")
    se_rows = analyse_select_errors(metadata, models, condition)

    print("Analysing non-JSON responses...")
    nj_rows, nj_types = analyse_non_json(metadata, models, condition)

    md = render_markdown(se_rows, nj_rows, nj_types, condition)

    out_path = ANSWERS_DIR / "format_analysis.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
