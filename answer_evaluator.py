#!/usr/bin/env python3
"""
Answer Evaluator — Evaluate model answers against ground truth.

Scans answers/{model}/default/ and evaluates each answer against
dataset/metadata/{qid}.json using type-specific metrics.

Usage:
    python answer_evaluator.py                          # evaluate all models
    python answer_evaluator.py --models google_gemini-3.1-flash-lite-preview
    python answer_evaluator.py --condition motivation    # evaluate motivation condition
    python answer_evaluator.py --force                   # re-evaluate even if results exist
"""

import click
import json
import math
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
DATASET_DIR = BASE_DIR / "dataset"
METADATA_DIR = DATASET_DIR / "metadata"
ANSWERS_DIR = BASE_DIR / "answers"

# ---------------------------------------------------------------------------
# Text normalisation helpers
# ---------------------------------------------------------------------------

def _norm(text: Any) -> str:
    """Normalise text for comparison: lowercase, strip, remove punctuation and accents."""
    if text is None:
        return ""
    s = str(text).strip().lower()
    # Normalise unicode (NFD), remove combining characters (accents)
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    # Remove punctuation
    s = re.sub(r"[^\w\s]", "", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _extract_ids(answer_list: Any) -> set:
    """Extract a set of IDs from an answer list."""
    if not answer_list or not isinstance(answer_list, list):
        return set()
    ids = set()
    for item in answer_list:
        if isinstance(item, dict):
            ids.add(str(item.get("id", "")).strip().upper())
        elif isinstance(item, str):
            ids.add(item.strip().upper())
    return ids - {""}


def _extract_checked_ids(answer_list: Any) -> set:
    """Extract IDs that are 'checked' (selected) from a checkbox answer list.

    Handles two response formats:
    1. TRUE/FALSE pattern: [{id:"A", text:"TRUE"}, {id:"B", text:"FALSE"}]
       -> returns only IDs marked TRUE/VERO
    2. Plain ID list: [{id:"A"}, {id:"C"}] or ["A", "C"]
       -> returns all IDs (same as _extract_ids)
    """
    if not answer_list or not isinstance(answer_list, list):
        return set()

    # Detect TRUE/FALSE pattern
    tf_values = {"TRUE", "FALSE", "VERO", "FALSO"}
    positive_values = {"TRUE", "VERO"}
    has_tf_pattern = False
    for item in answer_list:
        if isinstance(item, dict):
            text = str(item.get("text", "")).strip().upper()
            if text in tf_values:
                has_tf_pattern = True
                break

    if has_tf_pattern:
        ids = set()
        for item in answer_list:
            if isinstance(item, dict):
                text = str(item.get("text", "")).strip().upper()
                if text in positive_values:
                    aid = str(item.get("id", "")).strip().upper()
                    if aid:
                        ids.add(aid)
        return ids

    # Fallback: treat all IDs as selected
    return _extract_ids(answer_list)


def _extract_id_text_map(answer_list: Any) -> Dict[str, str]:
    """Extract {id: text/description} mapping from answer list."""
    if not answer_list or not isinstance(answer_list, list):
        return {}
    result = {}
    for item in answer_list:
        if isinstance(item, dict):
            aid = str(item.get("id", "")).strip().upper()
            text = item.get("text") or item.get("description") or ""
            if aid:
                result[aid] = str(text).strip()
    return result


def _f1_precision_recall(predicted: set, ground_truth: set) -> Dict[str, float]:
    """Compute F1, precision, recall over two sets."""
    if not predicted and not ground_truth:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not predicted or not ground_truth:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    tp = len(predicted & ground_truth)
    precision = tp / len(predicted) if predicted else 0.0
    recall = tp / len(ground_truth) if ground_truth else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


# ---------------------------------------------------------------------------
# Type-specific evaluators
# ---------------------------------------------------------------------------

def eval_multiple_choice_radio(llm_answer: Any, gt_answers: list, **kw) -> Dict:
    """Single correct option. Primary: exact match.

    If the LLM returns multiple IDs (wrong format), we check whether the
    ground truth is among the predicted set — giving credit if the correct
    answer was selected, even if extra options were also included.
    """
    gt_ids = _extract_ids(gt_answers)
    pred_ids = _extract_ids(llm_answer)

    gt_id = next(iter(gt_ids), "")

    # Credit if the correct answer is in the predicted set
    exact_match = 1.0 if gt_id and gt_id in pred_ids else 0.0

    # For reporting, show the single predicted ID when only one, else sorted list
    pred_display = sorted(pred_ids)[0] if len(pred_ids) == 1 else sorted(pred_ids)

    return {
        "exact_match": exact_match,
        "predicted": pred_display,
        "ground_truth": gt_id,
        "primary_metric": "exact_match",
        "primary_score": exact_match,
    }


def eval_multiple_choice_check(llm_answer: Any, gt_answers: list, **kw) -> Dict:
    """Set of correct options. Primary: F1."""
    gt_ids = _extract_ids(gt_answers)
    pred_ids = _extract_checked_ids(llm_answer)

    exact_match = 1.0 if pred_ids == gt_ids else 0.0
    prf = _f1_precision_recall(pred_ids, gt_ids)
    jaccard = len(pred_ids & gt_ids) / len(pred_ids | gt_ids) if (pred_ids | gt_ids) else 1.0

    return {
        "exact_match": exact_match,
        **prf,
        "jaccard": round(jaccard, 4),
        "predicted": sorted(pred_ids),
        "ground_truth": sorted(gt_ids),
        "primary_metric": "f1",
        "primary_score": prf["f1"],
    }


def eval_true_false(llm_answer: Any, gt_answers: list, **kw) -> Dict:
    """Multiple T/F statements. Primary: statement-level accuracy."""
    gt_map = _extract_id_text_map(gt_answers)  # {A: "True", B: "False", ...}
    pred_map = _extract_id_text_map(llm_answer)

    n_total = len(gt_map)
    if n_total == 0:
        return {"statement_accuracy": 0.0, "exact_match": 0.0,
                "primary_metric": "statement_accuracy", "primary_score": 0.0}

    n_correct = 0
    details = {}
    for sid, gt_val in gt_map.items():
        pred_val = pred_map.get(sid, "")
        gt_norm = _norm(gt_val)
        pred_norm = _norm(pred_val)
        # Normalise true/false/vero/falso
        gt_bool = gt_norm in ("true", "vero", "t", "v", "1")
        pred_bool = pred_norm in ("true", "vero", "t", "v", "1")
        correct = gt_bool == pred_bool
        if correct:
            n_correct += 1
        details[sid] = {"predicted": pred_val, "ground_truth": gt_val, "correct": correct}

    stmt_acc = n_correct / n_total
    exact_match = 1.0 if n_correct == n_total else 0.0

    return {
        "statement_accuracy": round(stmt_acc, 4),
        "exact_match": exact_match,
        "n_correct": n_correct,
        "n_total": n_total,
        "details": details,
        "primary_metric": "statement_accuracy",
        "primary_score": round(stmt_acc, 4),
    }


def eval_positioning(llm_answer: Any, gt_answers: list, **kw) -> Dict:
    """Ordered sequence or matching. Primary: element-level accuracy."""
    gt_map = _extract_id_text_map(gt_answers)
    pred_map = _extract_id_text_map(llm_answer)

    n_total = len(gt_map)
    if n_total == 0:
        return {"element_accuracy": 0.0, "exact_match": 0.0,
                "primary_metric": "element_accuracy", "primary_score": 0.0}

    n_correct = 0
    details = {}
    for sid, gt_val in gt_map.items():
        pred_val = pred_map.get(sid, "")
        correct = _norm(pred_val) == _norm(gt_val)
        if correct:
            n_correct += 1
        details[sid] = {"predicted": pred_val, "ground_truth": gt_val, "correct": correct}

    elem_acc = n_correct / n_total
    exact_match = 1.0 if n_correct == n_total else 0.0

    # Kendall's tau (if values are numeric or can be ordered)
    kendall_tau = None
    try:
        gt_order = [gt_map[k] for k in sorted(gt_map.keys())]
        pred_order = [pred_map.get(k, "") for k in sorted(gt_map.keys())]
        if all(v.isdigit() for v in gt_order) and all(v.isdigit() for v in pred_order if v):
            from scipy.stats import kendalltau
            gt_ranks = [int(v) for v in gt_order]
            pred_ranks = [int(v) if v.isdigit() else 0 for v in pred_order]
            tau, _ = kendalltau(gt_ranks, pred_ranks)
            kendall_tau = round(tau, 4) if not math.isnan(tau) else None
    except Exception:
        pass

    result = {
        "element_accuracy": round(elem_acc, 4),
        "exact_match": exact_match,
        "n_correct": n_correct,
        "n_total": n_total,
        "details": details,
        "primary_metric": "element_accuracy",
        "primary_score": round(elem_acc, 4),
    }
    if kendall_tau is not None:
        result["kendall_tau"] = kendall_tau
    return result


def eval_completion_closed(llm_answer: Any, gt_answers: list, **kw) -> Dict:
    """Fill blanks from word bank. Primary: blank-level accuracy."""
    gt_map = _extract_id_text_map(gt_answers)
    pred_map = _extract_id_text_map(llm_answer)

    n_total = len(gt_map)
    if n_total == 0:
        return {"blank_accuracy": 0.0, "exact_match": 0.0,
                "primary_metric": "blank_accuracy", "primary_score": 0.0}

    n_correct = 0
    details = {}
    for sid, gt_val in gt_map.items():
        pred_val = pred_map.get(sid, "")
        correct = _norm(pred_val) == _norm(gt_val)
        if correct:
            n_correct += 1
        details[sid] = {"predicted": pred_val, "ground_truth": gt_val, "correct": correct}

    blank_acc = n_correct / n_total
    exact_match = 1.0 if n_correct == n_total else 0.0

    return {
        "blank_accuracy": round(blank_acc, 4),
        "exact_match": exact_match,
        "n_correct": n_correct,
        "n_total": n_total,
        "details": details,
        "primary_metric": "blank_accuracy",
        "primary_score": round(blank_acc, 4),
    }


def eval_completion_open(llm_answer: Any, gt_answers: list, **kw) -> Dict:
    """Free-text short answer. Primary: blank-level fuzzy accuracy."""
    gt_map = _extract_id_text_map(gt_answers)
    pred_map = _extract_id_text_map(llm_answer)

    n_total = len(gt_map)
    if n_total == 0:
        return {"blank_accuracy": 0.0, "exact_match": 0.0,
                "primary_metric": "blank_accuracy", "primary_score": 0.0}

    n_correct = 0
    details = {}
    for sid, gt_val in gt_map.items():
        pred_val = pred_map.get(sid, "")
        # Fuzzy match: normalised comparison
        correct = _norm(pred_val) == _norm(gt_val)
        if correct:
            n_correct += 1
        details[sid] = {"predicted": pred_val, "ground_truth": gt_val, "correct": correct}

    blank_acc = n_correct / n_total
    exact_match = 1.0 if n_correct == n_total else 0.0

    return {
        "blank_accuracy": round(blank_acc, 4),
        "exact_match": exact_match,
        "n_correct": n_correct,
        "n_total": n_total,
        "details": details,
        "primary_metric": "blank_accuracy",
        "primary_score": round(blank_acc, 4),
        "note": "Uses normalised string matching. Consider LLM-as-judge for semantic evaluation.",
    }


def eval_select_errors(llm_answer: Any, gt_answers: list, **kw) -> Dict:
    """Identify errors in text. Primary: F1 over error set."""
    # Ground truth: list of {error, correct} pairs
    gt_errors = set()
    if isinstance(gt_answers, list):
        for item in gt_answers:
            if isinstance(item, dict):
                err = item.get("error", "")
                if err:
                    gt_errors.add(_norm(err))

    # Predicted: extract error terms from llm answer
    pred_errors = set()
    if isinstance(llm_answer, list):
        for item in llm_answer:
            if isinstance(item, dict):
                text = item.get("text") or item.get("error") or item.get("description") or ""
                if text:
                    pred_errors.add(_norm(text))
    elif isinstance(llm_answer, str):
        pred_errors.add(_norm(llm_answer))

    prf = _f1_precision_recall(pred_errors, gt_errors)
    exact_match = 1.0 if pred_errors == gt_errors else 0.0

    return {
        "exact_match": exact_match,
        **prf,
        "n_predicted": len(pred_errors),
        "n_ground_truth": len(gt_errors),
        "primary_metric": "f1",
        "primary_score": prf["f1"],
    }


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

EVALUATORS = {
    "multiple_choice_radio": eval_multiple_choice_radio,
    "multiple_choice_check": eval_multiple_choice_check,
    "true_false": eval_true_false,
    "positioning": eval_positioning,
    "completion_closed": eval_completion_closed,
    "completion_open": eval_completion_open,
    "select_errors": eval_select_errors,
}

ALL_CONDITIONS = ["default", "motivation"]


def evaluate_answer(qid: str, metadata: Dict, answer: Dict) -> Dict:
    """Evaluate a single answer against ground truth."""
    qtype = metadata.get("type", "")
    evaluator = EVALUATORS.get(qtype)

    if evaluator is None:
        return {
            "question_id": qid,
            "type": qtype,
            "error": f"Unknown question type: {qtype}",
            "primary_score": 0.0,
        }

    gt_answers = metadata.get("answers", [])
    llm_answer = answer.get("llm_answer")

    result = evaluator(llm_answer, gt_answers)
    result["question_id"] = qid
    result["type"] = qtype
    result["language"] = metadata.get("language", "")
    result["has_image"] = metadata.get("has_image", False)
    result["epistemic_level"] = metadata.get("epistemic_level", "")
    result["cultural_tradition"] = metadata.get("cultural_tradition", "")
    result["disciplinary_domain"] = metadata.get("disciplinary_domain", "")

    return result


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def _ci95_normal(values: List[float]) -> Tuple[float, float]:
    """95% CI using normal approximation: mean ± 1.96 * SE."""
    if len(values) < 2:
        return (0.0, 0.0)
    mean = np.mean(values)
    se = np.std(values, ddof=1) / np.sqrt(len(values))
    return (round(mean - 1.96 * se, 4), round(mean + 1.96 * se, 4))


def _ci95_wilson(values: List[float]) -> Tuple[float, float]:
    """95% CI using Wilson score interval (better for small n or extreme proportions)."""
    n = len(values)
    if n < 2:
        return (0.0, 0.0)
    p = np.mean(values)
    z = 1.96
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return (round(max(0.0, centre - margin), 4), round(min(1.0, centre + margin), 4))


def aggregate_results(results: List[Dict]) -> Dict:
    """Aggregate per-question results into summary tables."""

    # By type
    by_type = defaultdict(list)
    for r in results:
        by_type[r["type"]].append(r)

    type_summary = {}
    for qtype, items in sorted(by_type.items()):
        scores = [r["primary_score"] for r in items]
        primary_metric = items[0].get("primary_metric", "unknown") if items else "unknown"
        ci_normal = _ci95_normal(scores)
        ci_wilson = _ci95_wilson(scores)
        type_summary[qtype] = {
            "n": len(items),
            "primary_metric": primary_metric,
            "mean": round(float(np.mean(scores)), 4),
            "std": round(float(np.std(scores)), 4),
            "median": round(float(np.median(scores)), 4),
            "ci_95_lower": ci_normal[0],
            "ci_95_upper": ci_normal[1],
            "ci_95_wilson_lower": ci_wilson[0],
            "ci_95_wilson_upper": ci_wilson[1],
        }
        # Add type-specific extra metrics
        if qtype == "multiple_choice_check":
            type_summary[qtype]["mean_precision"] = round(np.mean([r.get("precision", 0) for r in items]), 4)
            type_summary[qtype]["mean_recall"] = round(np.mean([r.get("recall", 0) for r in items]), 4)
            type_summary[qtype]["mean_jaccard"] = round(np.mean([r.get("jaccard", 0) for r in items]), 4)
            type_summary[qtype]["exact_match_rate"] = round(np.mean([r.get("exact_match", 0) for r in items]), 4)
        elif qtype == "true_false":
            type_summary[qtype]["item_exact_match_rate"] = round(np.mean([r.get("exact_match", 0) for r in items]), 4)
        elif qtype == "positioning":
            type_summary[qtype]["exact_match_rate"] = round(np.mean([r.get("exact_match", 0) for r in items]), 4)
            taus = [r["kendall_tau"] for r in items if "kendall_tau" in r]
            if taus:
                type_summary[qtype]["mean_kendall_tau"] = round(np.mean(taus), 4)
        elif qtype == "select_errors":
            type_summary[qtype]["mean_precision"] = round(np.mean([r.get("precision", 0) for r in items]), 4)
            type_summary[qtype]["mean_recall"] = round(np.mean([r.get("recall", 0) for r in items]), 4)
            type_summary[qtype]["exact_match_rate"] = round(np.mean([r.get("exact_match", 0) for r in items]), 4)

    # Overall macro-averaged score (equal weight per type)
    type_means = [v["mean"] for v in type_summary.values()]
    macro_avg = round(float(np.mean(type_means)), 4) if type_means else 0.0

    # MCQ-only subset (radio only for clean comparison)
    mcq_items = [r for r in results if r["type"] == "multiple_choice_radio"]
    mcq_scores = [r["primary_score"] for r in mcq_items]
    mcq_ci = _ci95_normal(mcq_scores) if mcq_scores else (0.0, 0.0)
    mcq_summary = {
        "n": len(mcq_items),
        "exact_match_mean": round(float(np.mean(mcq_scores)), 4) if mcq_scores else 0.0,
        "ci_95_lower": mcq_ci[0],
        "ci_95_upper": mcq_ci[1],
    }

    # By epistemic level
    by_epistemic = defaultdict(list)
    for r in results:
        lvl = r.get("epistemic_level", "unknown") or "unknown"
        by_epistemic[lvl].append(r["primary_score"])
    epistemic_summary = {
        lvl: {"n": len(scores), "mean": round(float(np.mean(scores)), 4)}
        for lvl, scores in sorted(by_epistemic.items())
    }

    # By language
    by_lang = defaultdict(list)
    for r in results:
        by_lang[r.get("language", "unknown")].append(r["primary_score"])
    lang_summary = {
        lang: {"n": len(scores), "mean": round(float(np.mean(scores)), 4)}
        for lang, scores in sorted(by_lang.items())
    }

    # By has_image
    img_scores = [r["primary_score"] for r in results if r.get("has_image")]
    noimg_scores = [r["primary_score"] for r in results if not r.get("has_image")]
    image_summary = {
        "with_image": {"n": len(img_scores), "mean": round(float(np.mean(img_scores)), 4) if img_scores else 0.0},
        "without_image": {"n": len(noimg_scores), "mean": round(float(np.mean(noimg_scores)), 4) if noimg_scores else 0.0},
    }

    return {
        "total_evaluated": len(results),
        "macro_averaged_score": macro_avg,
        "by_type": type_summary,
        "mcq_subset": mcq_summary,
        "by_epistemic_level": epistemic_summary,
        "by_language": lang_summary,
        "by_image": image_summary,
    }


# ---------------------------------------------------------------------------
# CTT & IRT item analysis
# ---------------------------------------------------------------------------

def _build_response_matrix() -> Tuple[np.ndarray, List[str], List[str]]:
    """Build an (examinees × items) response matrix from all evaluations.

    Each model×condition pair is one examinee.  Items are question IDs.
    Cell values are primary_score (0–1, continuous for some types).

    Returns:
        matrix: np.ndarray of shape (n_examinees, n_items), NaN for missing
        examinee_labels: list of "model/condition" strings
        item_ids: list of question IDs (columns)
    """
    # Collect all per-question results
    examinee_data = {}  # {label: {qid: score}}
    for model_dir in sorted(ANSWERS_DIR.iterdir()):
        if not model_dir.is_dir() or model_dir.name.startswith("."):
            continue
        for cond in ALL_CONDITIONS:
            eval_file = model_dir / cond / "_evaluation.json"
            if not eval_file.exists():
                continue
            data = json.loads(eval_file.read_text(encoding="utf-8"))
            label = f"{model_dir.name}/{cond}"
            scores = {}
            for r in data["per_question"]:
                scores[r["question_id"]] = r["primary_score"]
            examinee_data[label] = scores

    if not examinee_data:
        return np.array([]), [], []

    # Union of all item IDs
    all_items = sorted(set().union(*examinee_data.values()))
    examinee_labels = sorted(examinee_data.keys())

    matrix = np.full((len(examinee_labels), len(all_items)), np.nan)
    for i, label in enumerate(examinee_labels):
        for j, qid in enumerate(all_items):
            if qid in examinee_data[label]:
                matrix[i, j] = examinee_data[label][qid]

    return matrix, examinee_labels, all_items


def _load_item_metadata(item_ids: List[str]) -> Dict[str, Dict]:
    """Load metadata for each item (type, language, etc.)."""
    meta = {}
    for qid in item_ids:
        f = METADATA_DIR / f"{qid}.json"
        if f.exists():
            meta[qid] = json.loads(f.read_text(encoding="utf-8"))
    return meta


def compute_ctt(matrix: np.ndarray, item_ids: List[str],
                examinee_labels: List[str]) -> List[Dict]:
    """Classical Test Theory analysis per item.

    Metrics:
        p_value (item difficulty): mean score across examinees (higher = easier)
        item_variance: variance of scores across examinees
        rpb (point-biserial discrimination): correlation of item score with
            total score (excluding that item) across examinees
        n_responses: number of non-NaN examinees for this item
    """
    n_examinees, n_items = matrix.shape
    # Total scores per examinee (mean of non-NaN items)
    examinee_totals = np.nanmean(matrix, axis=1)

    results = []
    for j in range(n_items):
        col = matrix[:, j]
        valid = ~np.isnan(col)
        n_resp = int(valid.sum())

        if n_resp < 2:
            results.append({
                "question_id": item_ids[j],
                "p_value": float(col[valid].mean()) if n_resp > 0 else np.nan,
                "item_variance": 0.0,
                "rpb": np.nan,
                "n_responses": n_resp,
            })
            continue

        scores = col[valid]
        p_val = float(scores.mean())
        var = float(scores.var(ddof=0))

        # Point-biserial: correlation between item score and total (excl. item)
        # Recompute totals excluding this item
        mask = np.ones(n_items, dtype=bool)
        mask[j] = False
        totals_excl = np.nanmean(matrix[:, mask], axis=1)
        totals_valid = totals_excl[valid]
        scores_valid = scores

        if np.std(scores_valid) > 0 and np.std(totals_valid) > 0:
            rpb = float(np.corrcoef(scores_valid, totals_valid)[0, 1])
        else:
            rpb = np.nan

        results.append({
            "question_id": item_ids[j],
            "p_value": round(p_val, 4),
            "item_variance": round(var, 4),
            "rpb": round(rpb, 4) if not np.isnan(rpb) else None,
            "n_responses": n_resp,
        })

    return results


def compute_irt_rasch(matrix: np.ndarray, item_ids: List[str],
                      examinee_labels: List[str],
                      max_iter: int = 500, tol: float = 1e-3) -> Dict:
    """Rasch model (1PL IRT) via Joint Maximum Likelihood Estimation.

    Estimates item difficulty (b) and examinee ability (theta) from
    binary/continuous [0,1] scores using JMLE on the logistic model:
        P(X=1 | theta, b) = 1 / (1 + exp(-(theta - b)))

    For continuous scores in [0,1] we treat them as probabilities
    (fractional responses) and optimise the expected log-likelihood.

    Items where all examinees score identically (p=0 or p=1) are
    excluded from estimation and marked as non-estimable.

    NOTE: With only ~8 examinees, parameters have large uncertainty.
    Interpret with caution.

    Returns dict with:
        items: [{question_id, b, se_b}, ...]
        examinees: [{label, theta}, ...]
        reliability: person separation reliability
        converged: bool
    """
    n_exam, n_items = matrix.shape
    B_MAX = 6.0  # clamp to prevent divergence on extreme items

    # Identify estimable items (need variance across examinees)
    estimable = np.zeros(n_items, dtype=bool)
    for j in range(n_items):
        col = matrix[:, j]
        valid = col[~np.isnan(col)]
        if len(valid) >= 2 and np.std(valid) > 0.01:
            estimable[j] = True

    est_idx = np.where(estimable)[0]
    n_est = len(est_idx)

    # Initialise
    theta = np.zeros(n_exam)
    b = np.zeros(n_items)

    # Use log-odds of means as initial estimates
    col_means = np.nanmean(matrix, axis=1)
    for i in range(n_exam):
        p = np.clip(col_means[i], 0.05, 0.95)
        theta[i] = np.log(p / (1 - p))
    item_means = np.nanmean(matrix, axis=0)
    for j in est_idx:
        p = np.clip(item_means[j], 0.05, 0.95)
        b[j] = -np.log(p / (1 - p))

    # For non-estimable items, set b based on mean score
    for j in range(n_items):
        if not estimable[j]:
            pm = np.nanmean(matrix[:, j])
            if np.isnan(pm):
                b[j] = 0.0
            elif pm >= 0.99:
                b[j] = -B_MAX  # very easy
            elif pm <= 0.01:
                b[j] = B_MAX   # very hard
            else:
                b[j] = -np.log(np.clip(pm, 0.05, 0.95) / (1 - np.clip(pm, 0.05, 0.95)))

    converged = False
    for iteration in range(max_iter):
        theta_old = theta.copy()
        b_old = b.copy()

        # Update theta (ability) given b — use only estimable items
        for i in range(n_exam):
            valid_mask = ~np.isnan(matrix[i, :]) & estimable
            if valid_mask.sum() == 0:
                continue
            x = matrix[i, valid_mask]
            bj = b[valid_mask]
            p = 1.0 / (1.0 + np.exp(-(theta[i] - bj)))
            p = np.clip(p, 1e-6, 1 - 1e-6)
            gradient = np.sum(x - p)
            info = np.sum(p * (1 - p))
            if info > 0:
                theta[i] += 0.5 * gradient / info  # damped Newton step

        # Centre theta (identification constraint)
        theta -= theta.mean()

        # Update b (difficulty) given theta — only estimable items
        for j in est_idx:
            valid = ~np.isnan(matrix[:, j])
            if valid.sum() == 0:
                continue
            x = matrix[valid, j]
            ti = theta[valid]
            p = 1.0 / (1.0 + np.exp(-(ti - b[j])))
            p = np.clip(p, 1e-6, 1 - 1e-6)
            gradient = -np.sum(x - p)
            info = np.sum(p * (1 - p))
            if info > 0:
                b[j] += 0.5 * gradient / info  # damped Newton step
                b[j] = np.clip(b[j], -B_MAX, B_MAX)

        # Check convergence (only on estimable items)
        if (np.max(np.abs(theta - theta_old)) < tol and
                np.max(np.abs(b[est_idx] - b_old[est_idx])) < tol):
            converged = True
            break

    # Standard errors for b (from Fisher information)
    se_b = np.full(n_items, np.nan)
    for j in est_idx:
        valid = ~np.isnan(matrix[:, j])
        if valid.sum() < 2:
            continue
        ti = theta[valid]
        p = 1.0 / (1.0 + np.exp(-(ti - b[j])))
        p = np.clip(p, 1e-6, 1 - 1e-6)
        info = np.sum(p * (1 - p))
        if info > 0:
            se_b[j] = 1.0 / np.sqrt(info)

    # Person separation reliability
    theta_var = np.var(theta, ddof=1) if n_exam > 1 else 0.0
    se_theta = []
    for i in range(n_exam):
        valid_mask = ~np.isnan(matrix[i, :]) & estimable
        bj = b[valid_mask]
        p = 1.0 / (1.0 + np.exp(-(theta[i] - bj)))
        p = np.clip(p, 1e-6, 1 - 1e-6)
        info = np.sum(p * (1 - p))
        se_theta.append(1.0 / np.sqrt(info) if info > 0 else np.nan)
    mse = np.nanmean(np.array(se_theta) ** 2)
    reliability = (theta_var - mse) / theta_var if theta_var > mse else 0.0

    items = []
    for j in range(n_items):
        items.append({
            "question_id": item_ids[j],
            "b": round(float(b[j]), 4),
            "se_b": round(float(se_b[j]), 4) if not np.isnan(se_b[j]) else None,
            "estimable": bool(estimable[j]),
        })

    examinees = []
    for i in range(n_exam):
        examinees.append({
            "label": examinee_labels[i],
            "theta": round(float(theta[i]), 4),
        })

    return {
        "items": items,
        "examinees": examinees,
        "reliability": round(float(reliability), 4),
        "converged": converged,
        "n_iterations": iteration + 1,
        "n_estimable": int(n_est),
        "n_non_estimable": int(n_items - n_est),
    }


def run_item_analysis() -> Optional[Dict]:
    """Run CTT and IRT analysis across all models and conditions.

    Saves results to answers/item_analysis.json and returns the dict.
    """
    matrix, examinee_labels, item_ids = _build_response_matrix()
    if matrix.size == 0:
        print("No data for item analysis.")
        return None

    n_exam, n_items = matrix.shape
    print(f"\nItem analysis: {n_exam} examinees × {n_items} items")

    # CTT
    ctt_results = compute_ctt(matrix, item_ids, examinee_labels)

    # IRT (Rasch)
    irt_results = compute_irt_rasch(matrix, item_ids, examinee_labels)
    print(f"  Rasch converged: {irt_results['converged']} "
          f"({irt_results['n_iterations']} iterations), "
          f"reliability: {irt_results['reliability']:.3f}, "
          f"estimable: {irt_results['n_estimable']}/{n_items}")

    # Merge CTT + IRT per item
    irt_by_qid = {r["question_id"]: r for r in irt_results["items"]}
    item_meta = _load_item_metadata(item_ids)

    items_combined = []
    for ctt in ctt_results:
        qid = ctt["question_id"]
        irt_item = irt_by_qid.get(qid, {})
        meta = item_meta.get(qid, {})
        items_combined.append({
            **ctt,
            "b": irt_item.get("b"),
            "se_b": irt_item.get("se_b"),
            "type": meta.get("type", ""),
            "language": meta.get("language", ""),
            "has_image": meta.get("has_image", False),
        })

    # Summary statistics
    p_values = [r["p_value"] for r in ctt_results if not np.isnan(r["p_value"])]
    rpbs = [r["rpb"] for r in ctt_results if r["rpb"] is not None]
    bs = [r["b"] for r in items_combined if r["b"] is not None]

    # Classify items by difficulty
    n_very_easy = sum(1 for p in p_values if p >= 0.9)
    n_easy = sum(1 for p in p_values if 0.7 <= p < 0.9)
    n_medium = sum(1 for p in p_values if 0.3 <= p < 0.7)
    n_hard = sum(1 for p in p_values if 0.1 <= p < 0.3)
    n_very_hard = sum(1 for p in p_values if p < 0.1)

    # Classify items by discrimination
    n_good_disc = sum(1 for r in rpbs if r >= 0.3)
    n_fair_disc = sum(1 for r in rpbs if 0.1 <= r < 0.3)
    n_poor_disc = sum(1 for r in rpbs if r < 0.1)

    summary = {
        "n_examinees": n_exam,
        "n_items": n_items,
        "examinee_labels": examinee_labels,
        "ctt": {
            "p_value": {
                "mean": round(float(np.mean(p_values)), 4),
                "std": round(float(np.std(p_values)), 4),
                "min": round(float(np.min(p_values)), 4),
                "max": round(float(np.max(p_values)), 4),
            },
            "rpb": {
                "mean": round(float(np.mean(rpbs)), 4) if rpbs else None,
                "std": round(float(np.std(rpbs)), 4) if rpbs else None,
                "min": round(float(np.min(rpbs)), 4) if rpbs else None,
                "max": round(float(np.max(rpbs)), 4) if rpbs else None,
            },
            "difficulty_distribution": {
                "very_easy_ge90": n_very_easy,
                "easy_70_90": n_easy,
                "medium_30_70": n_medium,
                "hard_10_30": n_hard,
                "very_hard_lt10": n_very_hard,
            },
            "discrimination_distribution": {
                "good_ge30": n_good_disc,
                "fair_10_30": n_fair_disc,
                "poor_lt10": n_poor_disc,
            },
        },
        "irt_rasch": {
            "converged": irt_results["converged"],
            "n_iterations": irt_results["n_iterations"],
            "reliability": irt_results["reliability"],
            "n_estimable": irt_results["n_estimable"],
            "n_non_estimable": irt_results["n_non_estimable"],
            "b_range": [round(float(np.min(bs)), 4), round(float(np.max(bs)), 4)] if bs else None,
            "examinees": irt_results["examinees"],
            "note": "Rasch (1PL) via JMLE. With N≤10 examinees, estimates have high uncertainty. "
                    "Items with zero variance across examinees are non-estimable.",
        },
    }

    # Print summary
    print(f"\n  CTT: mean p={summary['ctt']['p_value']['mean']:.3f}, "
          f"mean rpb={summary['ctt']['rpb']['mean']:.3f}")
    print(f"  Difficulty: {n_very_easy} very easy, {n_easy} easy, "
          f"{n_medium} medium, {n_hard} hard, {n_very_hard} very hard")
    print(f"  Discrimination: {n_good_disc} good, {n_fair_disc} fair, {n_poor_disc} poor")
    print(f"\n  IRT (Rasch) examinee abilities:")
    for e in irt_results["examinees"]:
        print(f"    {e['label']:55s} θ = {e['theta']:+.3f}")

    return {
        "summary": summary,
        "items": items_combined,
    }


# ---------------------------------------------------------------------------
# Advanced analyses: McNemar, breakdowns, logistic regression, diagnostics
# ---------------------------------------------------------------------------

def _load_all_evaluations(condition: str) -> Dict[str, List[Dict]]:
    """Load per_question results for all models in a condition.

    Returns {model_name: [per_question_result, ...]}
    """
    data = {}
    for model_dir in sorted(ANSWERS_DIR.iterdir()):
        if not model_dir.is_dir() or model_dir.name.startswith("."):
            continue
        eval_file = model_dir / condition / "_evaluation.json"
        if not eval_file.exists():
            continue
        ev = json.loads(eval_file.read_text(encoding="utf-8"))
        data[model_dir.name] = {r["question_id"]: r for r in ev["per_question"]}
    return data


def compute_mcnemar(condition: str, threshold: float = 0.5) -> Optional[Dict]:
    """McNemar's test for all model pairs within a condition.

    Binarises primary_score >= threshold as 'correct'.
    """
    from scipy.stats import chi2 as chi2_dist
    from itertools import combinations

    data = _load_all_evaluations(condition)
    if len(data) < 2:
        return None

    models = sorted(data.keys())
    all_qids = sorted(set().union(*(d.keys() for d in data.values())))

    results = []
    for m_a, m_b in combinations(models, 2):
        b = c = n_both = 0
        for qid in all_qids:
            if qid not in data[m_a] or qid not in data[m_b]:
                continue
            n_both += 1
            a_correct = data[m_a][qid]["primary_score"] >= threshold
            b_correct = data[m_b][qid]["primary_score"] >= threshold
            if a_correct and not b_correct:
                b += 1
            elif not a_correct and b_correct:
                c += 1

        n_disc = b + c
        if n_disc == 0:
            chi2_stat = 0.0
            p_val = 1.0
        elif n_disc < 25:
            # Exact binomial test
            from scipy.stats import binomtest
            bt = binomtest(b, n_disc, 0.5)
            chi2_stat = None
            p_val = bt.pvalue
        else:
            # McNemar with continuity correction
            chi2_stat = (abs(b - c) - 1) ** 2 / n_disc
            p_val = float(chi2_dist.sf(chi2_stat, 1))

        results.append({
            "model_a": m_a,
            "model_b": m_b,
            "n_paired": n_both,
            "b_a_right_b_wrong": b,
            "c_a_wrong_b_right": c,
            "chi2": round(chi2_stat, 4) if chi2_stat is not None else None,
            "p_value": round(p_val, 6),
            "significant_005": bool(p_val < 0.05),
            "favours": m_a if b > c else (m_b if c > b else "neither"),
        })

    output = {"condition": condition, "threshold": threshold, "comparisons": results}
    print(f"  McNemar ({condition}): {len(results)} pairs")
    return output


def compute_breakdown(condition: str, group_field: str) -> Optional[Dict]:
    """Per-model breakdown of primary_score by a grouping field.

    group_field: 'language', 'has_image', 'epistemic_level', etc.
    Returns {model: {group_value: {n, mean, std}}, ...} with t-test.
    """
    from scipy.stats import ttest_ind

    data = _load_all_evaluations(condition)
    if not data:
        return None

    results = {}
    for model, items in sorted(data.items()):
        groups = defaultdict(list)
        for qid, r in items.items():
            gval = r.get(group_field, "unknown")
            if gval is None:
                gval = "unknown"
            groups[str(gval)].append(r["primary_score"])

        # Skip if only one group or all "unknown"
        group_keys = sorted(groups.keys())
        if len(group_keys) < 2 or (len(group_keys) == 1 and group_keys[0] == "unknown"):
            continue

        model_result = {}
        for gval, scores in sorted(groups.items()):
            arr = np.array(scores)
            ci = _ci95_normal(arr) if len(arr) >= 2 else (0.0, 0.0)
            model_result[gval] = {
                "n": len(scores),
                "mean": round(float(arr.mean()), 4),
                "std": round(float(arr.std()), 4),
                "ci_95": [ci[0], ci[1]],
            }

        # Pairwise t-tests between groups (for 2-group case)
        if len(group_keys) == 2:
            g1, g2 = group_keys
            t_stat, p_val = ttest_ind(groups[g1], groups[g2], equal_var=False)
            model_result["_test"] = {
                "groups": [g1, g2],
                "t_stat": round(float(t_stat), 4),
                "p_value": round(float(p_val), 6),
                "significant_005": bool(float(p_val) < 0.05),
            }

        results[model] = model_result

    if not results:
        return None

    output = {"condition": condition, "group_field": group_field, "models": results}
    print(f"  Breakdown by {group_field} ({condition}): {len(results)} models")
    return output


def compute_logistic_regression(condition: str, threshold: float = 0.5) -> Optional[Dict]:
    """Logistic regression: P(correct) ~ question_type + has_image + language + model.

    Uses scipy.optimize.minimize with L-BFGS-B.
    """
    from scipy.optimize import minimize
    from scipy.stats import norm as norm_dist

    data = _load_all_evaluations(condition)
    if not data:
        return None

    models = sorted(data.keys())
    ref_model = models[0]

    # Collect observations: one row per (model, question)
    rows = []
    for model, items in data.items():
        for qid, r in items.items():
            rows.append({
                "y": 1 if r["primary_score"] >= threshold else 0,
                "type": r.get("type", "unknown"),
                "has_image": bool(r.get("has_image", False)),
                "language": r.get("language", "unknown"),
                "model": model,
            })

    if not rows:
        return None

    # Build design matrix with dummy encoding
    # Reference categories: multiple_choice_radio, has_image=False, language=en, first model
    all_types = sorted(set(r["type"] for r in rows))
    ref_type = "multiple_choice_radio" if "multiple_choice_radio" in all_types else all_types[0]
    type_dummies = [t for t in all_types if t != ref_type]

    all_langs = sorted(set(r["language"] for r in rows))
    ref_lang = "en" if "en" in all_langs else all_langs[0]
    lang_dummies = [l for l in all_langs if l != ref_lang]

    model_dummies = [m for m in models if m != ref_model]

    # Feature names
    feature_names = ["intercept"] + \
        [f"type:{t}" for t in type_dummies] + \
        ["has_image:True"] + \
        [f"language:{l}" for l in lang_dummies] + \
        [f"model:{m}" for m in model_dummies]

    n_features = len(feature_names)
    n_obs = len(rows)

    # Build X matrix
    X = np.zeros((n_obs, n_features))
    y = np.zeros(n_obs)

    for i, row in enumerate(rows):
        y[i] = row["y"]
        X[i, 0] = 1.0  # intercept
        col = 1
        for t in type_dummies:
            X[i, col] = 1.0 if row["type"] == t else 0.0
            col += 1
        X[i, col] = 1.0 if row["has_image"] else 0.0
        col += 1
        for l in lang_dummies:
            X[i, col] = 1.0 if row["language"] == l else 0.0
            col += 1
        for m in model_dummies:
            X[i, col] = 1.0 if row["model"] == m else 0.0
            col += 1

    # Logistic regression via MLE
    def neg_log_likelihood(beta):
        z = X @ beta
        z = np.clip(z, -30, 30)
        ll = np.sum(y * z - np.log(1 + np.exp(z)))
        return -ll

    def gradient(beta):
        z = X @ beta
        z = np.clip(z, -30, 30)
        p = 1.0 / (1.0 + np.exp(-z))
        return -X.T @ (y - p)

    # Optimise
    beta0 = np.zeros(n_features)
    result = minimize(neg_log_likelihood, beta0, jac=gradient, method="L-BFGS-B",
                      options={"maxiter": 1000})

    beta = result.x

    # Standard errors from Fisher information
    z_pred = X @ beta
    z_pred = np.clip(z_pred, -30, 30)
    p_pred = 1.0 / (1.0 + np.exp(-z_pred))
    W = p_pred * (1 - p_pred)
    H = X.T @ (X * W[:, np.newaxis])
    try:
        H_inv = np.linalg.inv(H)
        se = np.sqrt(np.diag(H_inv))
    except np.linalg.LinAlgError:
        se = np.full(n_features, np.nan)

    # z-scores and p-values
    z_scores = beta / se
    p_values = 2 * norm_dist.sf(np.abs(z_scores))
    odds_ratios = np.exp(beta)
    ci_lower = np.exp(beta - 1.96 * se)
    ci_upper = np.exp(beta + 1.96 * se)

    coefficients = []
    for j in range(n_features):
        coefficients.append({
            "predictor": feature_names[j],
            "coefficient": round(float(beta[j]), 4),
            "se": round(float(se[j]), 4) if not np.isnan(se[j]) else None,
            "z": round(float(z_scores[j]), 4) if not np.isnan(z_scores[j]) else None,
            "p_value": round(float(p_values[j]), 6) if not np.isnan(p_values[j]) else None,
            "odds_ratio": round(float(odds_ratios[j]), 4),
            "or_ci_lower": round(float(ci_lower[j]), 4) if not np.isnan(ci_lower[j]) else None,
            "or_ci_upper": round(float(ci_upper[j]), 4) if not np.isnan(ci_upper[j]) else None,
            "significant_005": bool(p_values[j] < 0.05) if not np.isnan(p_values[j]) else False,
        })

    output = {
        "condition": condition,
        "threshold": threshold,
        "n_observations": n_obs,
        "n_features": n_features,
        "converged": result.success,
        "reference_categories": {
            "question_type": ref_type,
            "has_image": False,
            "language": ref_lang,
            "model": ref_model,
        },
        "coefficients": coefficients,
    }

    print(f"  Logistic regression ({condition}): {n_features} predictors, n={n_obs}")
    return output


def compute_hardest_items_analysis(item_analysis: Dict) -> Optional[Dict]:
    """Identify and analyze items with p=0 or p<0.1 across all models."""
    if not item_analysis:
        return None

    items = item_analysis["items"]

    p_zero = [it for it in items if it["p_value"] == 0.0]
    p_low = [it for it in items if 0.0 < it["p_value"] < 0.1]

    # Flag suspicious: MCQ radio with p=0 (all models wrong)
    flags = []
    for it in p_zero:
        if it["type"] == "multiple_choice_radio":
            flags.append({
                "question_id": it["question_id"],
                "type": it["type"],
                "flag": "MCQ radio with p=0 — possible data error or extraction issue",
            })

    output = {
        "n_p_zero": len(p_zero),
        "n_p_low": len(p_low),
        "p_zero_items": p_zero,
        "p_low_items": p_low,
        "flags": flags,
    }

    print(f"  Hardest items: {len(p_zero)} p=0, {len(p_low)} p<0.1, {len(flags)} flags")
    return output


def compute_discrimination_by_type(item_analysis: Dict) -> Optional[Dict]:
    """rpb discrimination distribution per question type."""
    if not item_analysis:
        return None

    items = item_analysis["items"]

    by_type = defaultdict(list)
    for it in items:
        if it["rpb"] is not None:
            by_type[it["type"]].append(it["rpb"])

    results = {}
    for qtype, rpbs in sorted(by_type.items()):
        arr = np.array(rpbs)
        results[qtype] = {
            "n": len(rpbs),
            "mean": round(float(arr.mean()), 4),
            "std": round(float(arr.std()), 4),
            "median": round(float(np.median(arr)), 4),
            "min": round(float(arr.min()), 4),
            "max": round(float(arr.max()), 4),
            "good_ge30": int(np.sum(arr >= 0.3)),
            "fair_10_30": int(np.sum((arr >= 0.1) & (arr < 0.3))),
            "poor_lt10": int(np.sum(arr < 0.1)),
        }

    output = {"by_type": results}
    print(f"  Discrimination by type: {len(results)} types")
    return output


def run_advanced_analyses(item_analysis: Optional[Dict] = None) -> Dict:
    """Run all advanced analyses and return results in memory."""
    print(f"\n{'=' * 60}")
    print("Advanced analyses")
    print(f"{'=' * 60}")

    results = {"mcnemar": {}, "breakdowns": {}, "logistic": {}}

    for cond in ALL_CONDITIONS:
        eval_files = list(ANSWERS_DIR.glob(f"*/{cond}/_evaluation.json"))
        if not eval_files:
            continue

        results["mcnemar"][cond] = compute_mcnemar(cond)
        results["breakdowns"][(cond, "language")] = compute_breakdown(cond, "language")
        results["breakdowns"][(cond, "has_image")] = compute_breakdown(cond, "has_image")
        results["breakdowns"][(cond, "epistemic_level")] = compute_breakdown(cond, "epistemic_level")
        results["logistic"][cond] = compute_logistic_regression(cond)

    results["hardest_items"] = compute_hardest_items_analysis(item_analysis) if item_analysis else None
    results["discrimination_by_type"] = compute_discrimination_by_type(item_analysis) if item_analysis else None

    return results


# ---------------------------------------------------------------------------
# Main evaluation loop
# ---------------------------------------------------------------------------

def evaluate_model(model_dir: Path, condition: str, force: bool = False) -> Optional[Dict]:
    """Evaluate a single model's answers for a given condition."""
    condition_dir = model_dir / condition
    if not condition_dir.is_dir():
        return None

    model_name = model_dir.name
    output_file = condition_dir / "_evaluation.json"

    if output_file.exists() and not force:
        print(f"  {model_name}/{condition}: skip (exists, use --force)")
        return json.loads(output_file.read_text(encoding="utf-8"))

    # Load all metadata
    metadata = {}
    for f in sorted(METADATA_DIR.glob("*.json")):
        metadata[f.stem] = json.loads(f.read_text(encoding="utf-8"))

    # Evaluate each answer
    results = []
    n_missing = 0
    for qid in sorted(metadata.keys()):
        answer_file = condition_dir / f"{qid}.json"
        if not answer_file.exists():
            n_missing += 1
            continue
        answer = json.loads(answer_file.read_text(encoding="utf-8"))
        result = evaluate_answer(qid, metadata[qid], answer)
        results.append(result)

    if not results:
        print(f"  {model_name}/{condition}: no answers found")
        return None

    # Aggregate
    summary = aggregate_results(results)
    summary["model"] = model_name
    summary["condition"] = condition
    summary["n_missing"] = n_missing

    # Save
    output = {
        "summary": summary,
        "per_question": results,
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"  {model_name}/{condition}: {summary['total_evaluated']} evaluated, "
          f"macro={summary['macro_averaged_score']:.3f}, "
          f"MCQ={summary['mcq_subset']['exact_match_mean']:.3f}")
    for qtype, ts in summary["by_type"].items():
        print(f"    {qtype:25s} n={ts['n']:4d}  {ts['primary_metric']:25s} "
              f"mean={ts['mean']:.3f} [{ts['ci_95_lower']:.3f}, {ts['ci_95_upper']:.3f}]")

    return output


# ---------------------------------------------------------------------------
# Cross-model comparison table
# ---------------------------------------------------------------------------

def generate_comparison(condition: str):
    """Generate a cross-model comparison table from all evaluation files."""
    rows = []
    for model_dir in sorted(ANSWERS_DIR.iterdir()):
        if not model_dir.is_dir() or model_dir.name.startswith("."):
            continue
        eval_file = model_dir / condition / "_evaluation.json"
        if not eval_file.exists():
            continue
        data = json.loads(eval_file.read_text(encoding="utf-8"))
        s = data["summary"]
        row = {
            "model": s["model"],
            "n_evaluated": s["total_evaluated"],
            "macro_avg": s["macro_averaged_score"],
            "mcq_exact_match": s["mcq_subset"]["exact_match_mean"],
        }
        for qtype, ts in s["by_type"].items():
            row[f"{qtype}_mean"] = ts["mean"]
            row[f"{qtype}_n"] = ts["n"]
        rows.append(row)

    if not rows:
        print("No evaluation results found.")
        return

    # Sort by macro avg descending
    rows.sort(key=lambda r: r["macro_avg"], reverse=True)

    print(f"\nComparison table ({condition}): {len(rows)} models")

    # Print leaderboard
    print(f"\n{'Model':50s} {'Macro':>6s} {'MCQ':>6s} {'MC-chk':>6s} {'T/F':>6s} {'Pos':>6s} {'C-cls':>6s} {'C-opn':>6s} {'SelErr':>6s}")
    print("-" * 110)
    for r in rows:
        print(f"{r['model']:50s} "
              f"{r['macro_avg']:6.3f} "
              f"{r['mcq_exact_match']:6.3f} "
              f"{r.get('multiple_choice_check_mean', 0):6.3f} "
              f"{r.get('true_false_mean', 0):6.3f} "
              f"{r.get('positioning_mean', 0):6.3f} "
              f"{r.get('completion_closed_mean', 0):6.3f} "
              f"{r.get('completion_open_mean', 0):6.3f} "
              f"{r.get('select_errors_mean', 0):6.3f}")


# ---------------------------------------------------------------------------
# Type display config (shared)
# ---------------------------------------------------------------------------

TYPE_COLS = [
    ("multiple_choice_radio", "MCQ Radio", "Exact Match"),
    ("multiple_choice_check", "MCQ Check", "F1"),
    ("true_false", "True/False", "Stmt Accuracy"),
    ("positioning", "Positioning", "Element Accuracy"),
    ("completion_closed", "Completion (Closed)", "Blank Accuracy"),
    ("completion_open", "Completion (Open)", "Blank Accuracy"),
    ("select_errors", "Select Errors", "F1"),
]


def _collect_condition_rows(cond: str) -> List[Dict]:
    """Collect evaluation rows for a condition across all models."""
    cond_rows = []
    for model_dir in sorted(ANSWERS_DIR.iterdir()):
        if not model_dir.is_dir() or model_dir.name.startswith("."):
            continue
        eval_file = model_dir / cond / "_evaluation.json"
        if not eval_file.exists():
            continue
        data = json.loads(eval_file.read_text(encoding="utf-8"))
        s = data["summary"]
        row = {"model": s["model"], "n_evaluated": s["total_evaluated"],
               "macro_avg": s["macro_averaged_score"] * 100,
               "mcq_exact_match": s["mcq_subset"]["exact_match_mean"] * 100}
        for qtype, ts in s["by_type"].items():
            row[f"{qtype}_mean"] = ts["mean"] * 100
            row[f"{qtype}_n"] = ts["n"]
            row[f"{qtype}_ci_wilson"] = f"[{ts['ci_95_wilson_lower']*100:.1f}%, {ts['ci_95_wilson_upper']*100:.1f}%]"
        cond_rows.append(row)
    cond_rows.sort(key=lambda r: r["macro_avg"], reverse=True)
    return cond_rows


def _render_condition_section(cond: str, cond_rows: List[Dict]) -> List[str]:
    """Render markdown section for a single condition."""
    lines = []

    # Leaderboard table
    lines.append("## Leaderboard (Macro-Averaged Score)")
    lines.append("")
    lines.append("| Rank | Model | Macro Avg | MCQ Exact Match | N Evaluated |")
    lines.append("|------|-------|-----------|-----------------|-------------|")
    for i, r in enumerate(cond_rows, 1):
        lines.append(f"| {i} | `{r['model']}` | **{r['macro_avg']:.1f}%** | {r['mcq_exact_match']:.1f}% | {r['n_evaluated']} |")
    lines.append("")

    # Per-type table
    lines.append("## Results by Question Type")
    lines.append("")
    header = "| Model |"
    sep = "|-------|"
    for _, label, metric in TYPE_COLS:
        header += f" {label} ({metric}) |"
        sep += "------|"
    lines.append(header)
    lines.append(sep)

    for r in cond_rows:
        row_str = f"| `{r['model']}` |"
        for type_key, _, _ in TYPE_COLS:
            val = r.get(f"{type_key}_mean")
            n = r.get(f"{type_key}_n", 0)
            if val is not None and n > 0:
                row_str += f" {val:.1f}% (n={n}) |"
            else:
                row_str += " — |"
        lines.append(row_str)
    lines.append("")

    # Per-type detailed with CI
    lines.append("## Detailed Results with 95% CI")
    lines.append("")
    for type_key, label, metric in TYPE_COLS:
        has_data = any(r.get(f"{type_key}_n", 0) > 0 for r in cond_rows)
        if not has_data:
            continue
        lines.append(f"**{label}** (Primary metric: {metric})")
        lines.append("")
        lines.append("| Model | Mean | 95% CI | N |")
        lines.append("|-------|------|--------|---|")
        for r in cond_rows:
            val = r.get(f"{type_key}_mean")
            n = r.get(f"{type_key}_n", 0)
            ci_w = r.get(f"{type_key}_ci_wilson", "")
            if val is not None and n > 0:
                lines.append(f"| `{r['model']}` | {val:.1f}% | {ci_w} | {n} |")
        lines.append("")

    return lines


def _render_cross_condition_section(comparison: Optional[List[Dict]] = None) -> List[str]:
    """Render the cross-condition comparison section for the README."""
    if not comparison:
        return []

    lines = []
    lines.append("## Cross-Condition Comparison: `default` vs `motivation`")
    lines.append("")
    lines.append("Paired comparison on questions answered under both conditions. "
                  "The motivation condition adds chain-of-thought reasoning to the prompt.")
    lines.append("")

    # Overall table
    lines.append("### Overall (Paired Scores)")
    lines.append("")
    lines.append("| Model | N Paired | Default | Motivation | Diff | 95% CI | p-value | Improved | Same | Degraded |")
    lines.append("|-------|----------|---------|------------|------|--------|---------|----------|------|----------|")
    for r in comparison:
        diff_str = f"{r['mean_diff']*100:+.1f}pp"
        ci_str = f"[{r['ci_95_lower']*100:+.1f}, {r['ci_95_upper']*100:+.1f}]pp"
        sig = " \\*" if r["p_value"] < 0.05 else ""
        lines.append(
            f"| `{r['model']}` | {r['n_paired']} | {r['default_mean']*100:.1f}% | "
            f"{r['motivation_mean']*100:.1f}% | {diff_str} | {ci_str} | "
            f"{r['p_value']:.3f}{sig} | {r['n_improved']} | {r['n_same']} | {r['n_degraded']} |"
        )
    lines.append("")

    # Per-type breakdown
    lines.append("### By Question Type (Paired)")
    lines.append("")
    lines.append("| Model | Type | N | Default | Motivation | Diff |")
    lines.append("|-------|------|---|---------|------------|------|")
    for r in comparison:
        for qtype, ts in sorted(r["by_type"].items()):
            type_label = next((label for key, label, _ in TYPE_COLS if key == qtype), qtype)
            diff_str = f"{ts['mean_diff']*100:+.1f}pp"
            lines.append(
                f"| `{r['model']}` | {type_label} | {ts['n_paired']} | "
                f"{ts['default_mean']*100:.1f}% | {ts['motivation_mean']*100:.1f}% | {diff_str} |"
            )
    lines.append("")

    lines.append("> **Note**: Diff is in percentage points (pp). "
                 "p-values from paired t-test. \\* = significant at α=0.05.")
    lines.append("")

    return lines


def _render_item_analysis_section(ia_data: Optional[Dict] = None) -> List[str]:
    """Render the CTT/IRT item analysis section for the README."""
    if not ia_data:
        return []

    s = ia_data["summary"]
    items = ia_data["items"]

    lines = []
    lines.append("## Item Analysis (CTT & IRT)")
    lines.append("")
    lines.append(f"Analysis across **{s['n_examinees']} examinees** "
                 f"(model × condition) and **{s['n_items']} items**.")
    lines.append("")

    # CTT summary
    lines.append("### Classical Test Theory (CTT)")
    lines.append("")
    ctt = s["ctt"]
    lines.append("| Statistic | Mean | SD | Min | Max |")
    lines.append("|-----------|------|----|-----|-----|")
    pv = ctt["p_value"]
    lines.append(f"| Item Difficulty (p) | {pv['mean']:.3f} | {pv['std']:.3f} | {pv['min']:.3f} | {pv['max']:.3f} |")
    rpb = ctt["rpb"]
    if rpb["mean"] is not None:
        lines.append(f"| Discrimination (r_pb) | {rpb['mean']:.3f} | {rpb['std']:.3f} | {rpb['min']:.3f} | {rpb['max']:.3f} |")
    lines.append("")

    # Difficulty distribution
    dd = ctt["difficulty_distribution"]
    lines.append("**Item Difficulty Distribution**")
    lines.append("")
    lines.append("| Category | p Range | Count |")
    lines.append("|----------|---------|-------|")
    lines.append(f"| Very Easy | ≥ 0.90 | {dd['very_easy_ge90']} |")
    lines.append(f"| Easy | 0.70 – 0.89 | {dd['easy_70_90']} |")
    lines.append(f"| Medium | 0.30 – 0.69 | {dd['medium_30_70']} |")
    lines.append(f"| Hard | 0.10 – 0.29 | {dd['hard_10_30']} |")
    lines.append(f"| Very Hard | < 0.10 | {dd['very_hard_lt10']} |")
    lines.append("")

    # Discrimination distribution
    disc = ctt["discrimination_distribution"]
    lines.append("**Item Discrimination Distribution**")
    lines.append("")
    lines.append("| Category | r_pb Range | Count |")
    lines.append("|----------|------------|-------|")
    lines.append(f"| Good | ≥ 0.30 | {disc['good_ge30']} |")
    lines.append(f"| Fair | 0.10 – 0.29 | {disc['fair_10_30']} |")
    lines.append(f"| Poor | < 0.10 | {disc['poor_lt10']} |")
    lines.append("")

    # IRT Rasch
    irt = s["irt_rasch"]
    lines.append("### Item Response Theory — Rasch Model (1PL)")
    lines.append("")
    lines.append(f"- Converged: {'Yes' if irt['converged'] else 'No'} "
                 f"({irt['n_iterations']} iterations)")
    lines.append(f"- Person Separation Reliability: {irt['reliability']:.3f}")
    lines.append(f"- Estimable items: {irt.get('n_estimable', '?')} / "
                 f"{irt.get('n_estimable', 0) + irt.get('n_non_estimable', 0)} "
                 f"({irt.get('n_non_estimable', '?')} items with zero variance excluded)")
    if irt["b_range"]:
        lines.append(f"- Item difficulty (b) range: [{irt['b_range'][0]:.2f}, {irt['b_range'][1]:.2f}]")
    lines.append("")

    lines.append("**Examinee Ability Estimates (θ)**")
    lines.append("")
    lines.append("| Model / Condition | θ |")
    lines.append("|-------------------|---|")
    for e in sorted(irt["examinees"], key=lambda x: -x["theta"]):
        lines.append(f"| `{e['label']}` | {e['theta']:+.3f} |")
    lines.append("")

    # Hardest and easiest items (only estimable for IRT columns)
    sorted_by_p = sorted(items, key=lambda x: x["p_value"])
    lines.append("**10 Hardest Items** (lowest p-value)")
    lines.append("")
    lines.append("| Question | Type | p | r_pb | b (Rasch) |")
    lines.append("|----------|------|---|------|-----------|")
    for it in sorted_by_p[:10]:
        rpb_str = f"{it['rpb']:.3f}" if it["rpb"] is not None else "—"
        b_str = f"{it['b']:.2f}" if it["b"] is not None else "—"
        lines.append(f"| {it['question_id']} | {it['type']} | {it['p_value']:.3f} | {rpb_str} | {b_str} |")
    lines.append("")

    lines.append("**10 Easiest Items** (highest p-value)")
    lines.append("")
    lines.append("| Question | Type | p | r_pb | b (Rasch) |")
    lines.append("|----------|------|---|------|-----------|")
    for it in sorted_by_p[-10:]:
        rpb_str = f"{it['rpb']:.3f}" if it["rpb"] is not None else "—"
        b_str = f"{it['b']:.2f}" if it["b"] is not None else "—"
        lines.append(f"| {it['question_id']} | {it['type']} | {it['p_value']:.3f} | {rpb_str} | {b_str} |")
    lines.append("")

    # Most discriminating items
    sorted_by_rpb = sorted(
        [it for it in items if it["rpb"] is not None],
        key=lambda x: x["rpb"], reverse=True
    )
    if sorted_by_rpb:
        lines.append("**10 Most Discriminating Items** (highest r_pb)")
        lines.append("")
        lines.append("| Question | Type | p | r_pb | b (Rasch) |")
        lines.append("|----------|------|---|------|-----------|")
        for it in sorted_by_rpb[:10]:
            b_str = f"{it['b']:.2f}" if it["b"] is not None else "—"
            lines.append(f"| {it['question_id']} | {it['type']} | {it['p_value']:.3f} | {it['rpb']:.3f} | {b_str} |")
        lines.append("")

    lines.append(f"> **Note**: {irt['note']}")
    lines.append("")

    return lines


def _render_mcnemar_section(mcnemar_data: Optional[Dict[str, Dict]] = None) -> List[str]:
    """Render McNemar's test results for the README."""
    if not mcnemar_data:
        return []
    lines = []
    any_found = False
    for cond in ALL_CONDITIONS:
        data = mcnemar_data.get(cond)
        if not data:
            continue
        any_found = True

        lines.append(f"## Cross-Model Comparison — McNemar's Test (`{cond}`)")
        lines.append("")
        lines.append("Pairwise test of whether two models differ significantly on the same items "
                      f"(binarised at score ≥ {data['threshold']}).")
        lines.append("")
        lines.append("| Model A | Model B | N | A✓B✗ | A✗B✓ | χ² | p-value | Favours |")
        lines.append("|---------|---------|---|------|------|----|---------|---------| ")
        for c in data["comparisons"]:
            chi2_str = f"{c['chi2']:.2f}" if c["chi2"] is not None else "exact"
            sig = " \\*" if c["significant_005"] else ""
            lines.append(
                f"| `{c['model_a']}` | `{c['model_b']}` | {c['n_paired']} | "
                f"{c['b_a_right_b_wrong']} | {c['c_a_wrong_b_right']} | "
                f"{chi2_str} | {c['p_value']:.4f}{sig} | {c['favours']} |"
            )
        lines.append("")
        lines.append("> McNemar's test with continuity correction (exact binomial if n<25 discordant pairs). "
                      "\\* = significant at α=0.05.")
        lines.append("")

    return lines if any_found else []


def _render_breakdown_sections(breakdowns: Optional[Dict] = None) -> List[str]:
    """Render language and image breakdown sections for the README."""
    if not breakdowns:
        return []
    lines = []

    for cond in ALL_CONDITIONS:
        for field, title in [("language", "Language"), ("has_image", "Image Presence")]:
            data = breakdowns.get((cond, field))
            if not data:
                continue
            models = data.get("models", {})
            if not models:
                continue

            lines.append(f"## Breakdown by {title} (`{cond}`)")
            lines.append("")

            # Get group columns from first model
            first_model_data = next(iter(models.values()))
            groups = sorted(k for k in first_model_data.keys() if not k.startswith("_"))

            header = "| Model |"
            sep = "|-------|"
            for g in groups:
                header += f" {g} |"
                sep += "------|"
            lines.append(header)
            lines.append(sep)

            for model, mdata in sorted(models.items()):
                row = f"| `{model}` |"
                for g in groups:
                    gd = mdata.get(g, {})
                    if gd:
                        row += f" {gd['mean']*100:.1f}% (n={gd['n']}) |"
                    else:
                        row += " — |"
                lines.append(row)

            # Show t-test if available
            test_data = None
            for model, mdata in models.items():
                if "_test" in mdata:
                    test_data = mdata["_test"]
                    break
            if test_data:
                lines.append("")
                lines.append(f"> Welch t-test per model comparing groups. "
                             f"Example: {test_data['groups'][0]} vs {test_data['groups'][1]}.")

            lines.append("")

    return lines


def _render_logistic_regression_section(logistic_data: Optional[Dict[str, Dict]] = None) -> List[str]:
    """Render logistic regression results for the README."""
    if not logistic_data:
        return []
    lines = []

    for cond in ALL_CONDITIONS:
        data = logistic_data.get(cond)
        if not data:
            continue

        lines.append(f"## Logistic Regression (`{cond}`)")
        lines.append("")
        ref = data["reference_categories"]
        lines.append(f"P(correct) ~ question_type + has_image + language + model "
                      f"(n={data['n_observations']:,}, threshold={data['threshold']})")
        lines.append("")
        lines.append(f"Reference categories: type=`{ref['question_type']}`, "
                      f"has_image={ref['has_image']}, language=`{ref['language']}`, "
                      f"model=`{ref['model']}`")
        lines.append("")
        lines.append("| Predictor | β | SE | z | p | OR | 95% CI |")
        lines.append("|-----------|---|----|----|---|----|---------| ")

        for c in data["coefficients"]:
            sig = " \\*" if c["significant_005"] else ""
            se_str = f"{c['se']:.3f}" if c["se"] is not None else "—"
            z_str = f"{c['z']:.2f}" if c["z"] is not None else "—"
            p_str = f"{c['p_value']:.4f}" if c["p_value"] is not None else "—"
            ci_str = f"[{c['or_ci_lower']:.2f}, {c['or_ci_upper']:.2f}]" if c["or_ci_lower"] is not None else "—"
            lines.append(
                f"| {c['predictor']} | {c['coefficient']:.3f} | {se_str} | "
                f"{z_str} | {p_str}{sig} | {c['odds_ratio']:.3f} | {ci_str} |"
            )
        lines.append("")
        lines.append("> OR > 1 means higher odds of correct answer vs reference. "
                      "\\* = p < 0.05.")
        lines.append("")

    return lines


def _render_hardest_items_section(hardest_data: Optional[Dict] = None) -> List[str]:
    """Render hardest items analysis for the README."""
    if not hardest_data:
        return []
    data = hardest_data

    lines = []
    lines.append("## Hardest Items (p = 0)")
    lines.append("")
    lines.append(f"**{data['n_p_zero']}** items scored 0 across all models and conditions. "
                 f"**{data['n_p_low']}** additional items scored p < 0.10.")
    lines.append("")

    if data["flags"]:
        lines.append(f"**{len(data['flags'])} flagged for review** (MCQ radio with p=0 — "
                     "possible data or extraction errors):")
        lines.append("")
        lines.append("| Question | Type | Flag |")
        lines.append("|----------|------|------|")
        for f in data["flags"]:
            lines.append(f"| {f['question_id']} | {f['type']} | {f['flag']} |")
        lines.append("")

    return lines


def _render_discrimination_by_type_section(disc_data: Optional[Dict] = None) -> List[str]:
    """Render discrimination distribution per question type for the README."""
    if not disc_data:
        return []
    data = disc_data

    lines = []
    lines.append("## Item Discrimination by Question Type")
    lines.append("")
    lines.append("| Type | N | Mean r_pb | Median | Good (≥.30) | Fair (.10–.29) | Poor (<.10) |")
    lines.append("|------|---|-----------|--------|-------------|----------------|-------------|")
    for qtype, d in sorted(data["by_type"].items()):
        lines.append(
            f"| {qtype} | {d['n']} | {d['mean']:.3f} | {d['median']:.3f} | "
            f"{d['good_ge30']} | {d['fair_10_30']} | {d['poor_lt10']} |"
        )
    lines.append("")
    lines.append("> Higher mean r_pb indicates better discrimination between strong and weak examinees. "
                 "MCQ check tends to produce more continuous scores, inflating correlation.")
    lines.append("")

    return lines


def generate_readme_all():
    """Generate the full README from in-memory data. Only output is README.md."""
    from datetime import datetime

    # Collect condition rows
    default_rows = _collect_condition_rows("default")

    # Run item analysis
    item_analysis = run_item_analysis()

    # Run cross-condition comparison
    cross_cond = generate_cross_condition_comparison()

    # Run advanced analyses
    advanced = run_advanced_analyses(item_analysis)

    lines = [
        "# Evaluation Results",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Metrics Overview",
        "",
        "Each question type uses a specific metric depending on the task:",
        "",
        "- **Single-choice questions** → Exact Match (binary, cleanest metric).",
        "- **Multi-choice and error detection** → F1 score (balances precision and recall).",
        "- **True/False** → evaluated per statement (not per item) to avoid bias from longer questions.",
        "- **Positioning and completion tasks** → accuracy per element/blank.",
        "- **Open-text completion** is stricter (exact matching), so results should be interpreted with caution.",
        "",
    ]

    # Only render the default condition (no condition header)
    if default_rows:
        lines.extend(_render_condition_section("default", default_rows))

    # Cross-condition comparison
    lines.extend(_render_cross_condition_section(cross_cond))

    # Item analysis (CTT & IRT)
    lines.extend(_render_item_analysis_section(item_analysis))

    # Advanced analyses
    lines.extend(_render_mcnemar_section(advanced.get("mcnemar")))
    lines.extend(_render_breakdown_sections(advanced.get("breakdowns")))
    lines.extend(_render_logistic_regression_section(advanced.get("logistic")))
    lines.extend(_render_hardest_items_section(advanced.get("hardest_items")))
    lines.extend(_render_discrimination_by_type_section(advanced.get("discrimination_by_type")))

    # Metric definitions
    lines.extend([
        "## Metric Definitions",
        "",
        "| Question Type | Primary Metric | Description |",
        "|---------------|----------------|-------------|",
        "| multiple_choice_radio | Exact Match | 1 if predicted = ground truth, 0 otherwise |",
        "| multiple_choice_check | F1 Score | Harmonic mean of precision and recall over selected options |",
        "| true_false | Statement Accuracy | Proportion of individual T/F statements correct |",
        "| positioning | Element Accuracy | Proportion of elements correctly placed |",
        "| completion_closed | Blank Accuracy | Proportion of blanks correctly filled (fuzzy match) |",
        "| completion_open | Blank Accuracy | Proportion of blanks correct (normalised string match) |",
        "| select_errors | F1 Score | F1 over identified error set vs ground truth |",
        "",
        "### Aggregate Scores",
        "",
        "- **Macro Average**: Mean of per-type primary metrics with equal weight per type",
        "- **MCQ Exact Match**: Exact match on multiple_choice_radio items only (cleanest subset)",
        "- **95% CI**: Wilson score interval — better coverage for small samples and extreme proportions",
        "",
    ])

    readme_path = ANSWERS_DIR / "README.md"
    readme_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"README: {readme_path}")


# ---------------------------------------------------------------------------
# Cross-condition comparison (default vs motivation)
# ---------------------------------------------------------------------------

def _load_condition_summaries(condition: str) -> Dict[str, Dict]:
    """Load evaluation summaries for all models in a given condition.
    Returns {model_name: summary_dict}."""
    summaries = {}
    for model_dir in sorted(ANSWERS_DIR.iterdir()):
        if not model_dir.is_dir() or model_dir.name.startswith("."):
            continue
        eval_file = model_dir / condition / "_evaluation.json"
        if not eval_file.exists():
            continue
        data = json.loads(eval_file.read_text(encoding="utf-8"))
        summaries[model_dir.name] = data["summary"]
    return summaries


def generate_cross_condition_comparison():
    """Compare default vs motivation conditions per model using paired questions."""
    print("\n" + "=" * 60)
    print("Cross-condition comparison: default vs motivation")
    print("=" * 60)

    # Load per-question results for both conditions
    paired_data = {}  # {model: {qid: {default: score, motivation: score}}}
    condition_summaries = {}  # {condition: {model: summary}}

    for cond in ALL_CONDITIONS:
        condition_summaries[cond] = _load_condition_summaries(cond)

    # Find models present in both conditions
    models_both = sorted(
        set(condition_summaries.get("default", {}).keys())
        & set(condition_summaries.get("motivation", {}).keys())
    )

    if not models_both:
        print("No models found with both conditions evaluated.")
        return

    # Load per-question results and pair them
    for model in models_both:
        paired_data[model] = {}
        per_q = {}  # {qid: {cond: result}}
        for cond in ALL_CONDITIONS:
            eval_file = ANSWERS_DIR / model / cond / "_evaluation.json"
            if not eval_file.exists():
                continue
            data = json.loads(eval_file.read_text(encoding="utf-8"))
            for r in data["per_question"]:
                qid = r["question_id"]
                if qid not in per_q:
                    per_q[qid] = {}
                per_q[qid][cond] = r

        # Keep only questions present in both conditions
        for qid, cond_results in per_q.items():
            if "default" in cond_results and "motivation" in cond_results:
                paired_data[model][qid] = {
                    "default": cond_results["default"]["primary_score"],
                    "motivation": cond_results["motivation"]["primary_score"],
                    "type": cond_results["default"]["type"],
                }

    # Build comparison results
    comparison = []
    for model in models_both:
        pairs = paired_data[model]
        if not pairs:
            continue

        n_paired = len(pairs)
        default_scores = [p["default"] for p in pairs.values()]
        motivation_scores = [p["motivation"] for p in pairs.values()]
        diffs = [p["motivation"] - p["default"] for p in pairs.values()]

        mean_default = float(np.mean(default_scores))
        mean_motivation = float(np.mean(motivation_scores))
        mean_diff = float(np.mean(diffs))
        se_diff = float(np.std(diffs, ddof=1) / np.sqrt(n_paired)) if n_paired > 1 else 0.0

        # Paired t-test
        from scipy.stats import ttest_rel
        if n_paired > 1 and np.std(diffs) > 0:
            t_stat, p_value = ttest_rel(motivation_scores, default_scores)
        else:
            t_stat, p_value = 0.0, 1.0

        # Per-type breakdown (paired)
        by_type = defaultdict(lambda: {"default": [], "motivation": [], "diffs": []})
        for p in pairs.values():
            by_type[p["type"]]["default"].append(p["default"])
            by_type[p["type"]]["motivation"].append(p["motivation"])
            by_type[p["type"]]["diffs"].append(p["motivation"] - p["default"])

        type_comparison = {}
        for qtype, scores in sorted(by_type.items()):
            n_t = len(scores["diffs"])
            type_comparison[qtype] = {
                "n_paired": n_t,
                "default_mean": round(float(np.mean(scores["default"])), 4),
                "motivation_mean": round(float(np.mean(scores["motivation"])), 4),
                "mean_diff": round(float(np.mean(scores["diffs"])), 4),
            }

        # Count improved / same / degraded
        n_improved = sum(1 for d in diffs if d > 0)
        n_same = sum(1 for d in diffs if d == 0)
        n_degraded = sum(1 for d in diffs if d < 0)

        row = {
            "model": model,
            "n_paired": n_paired,
            "default_mean": round(mean_default, 4),
            "motivation_mean": round(mean_motivation, 4),
            "mean_diff": round(mean_diff, 4),
            "se_diff": round(se_diff, 4),
            "ci_95_lower": round(mean_diff - 1.96 * se_diff, 4),
            "ci_95_upper": round(mean_diff + 1.96 * se_diff, 4),
            "t_stat": round(float(t_stat), 4),
            "p_value": round(float(p_value), 4),
            "n_improved": n_improved,
            "n_same": n_same,
            "n_degraded": n_degraded,
            "by_type": type_comparison,
        }
        comparison.append(row)

        # Print
        sig = "*" if p_value < 0.05 else ""
        direction = "+" if mean_diff > 0 else ""
        print(f"  {model}: default={mean_default:.3f}, motivation={mean_motivation:.3f}, "
              f"diff={direction}{mean_diff:.3f} (p={p_value:.3f}{sig}), "
              f"n={n_paired} [+{n_improved}/={n_same}/-{n_degraded}]")

    print(f"\nCross-condition comparison: {len(comparison)} models")
    return comparison


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.command()
@click.option("--models", multiple=True, help="Model directory names to evaluate (default: all)")
@click.option("--condition", default="all", help="Prompt condition: default, motivation, or all (default: all)")
@click.option("--force", is_flag=True, help="Re-evaluate even if results exist")
@click.option("--compare-only", is_flag=True, help="Only generate comparison table from existing evaluations")
def main(models, condition, force, compare_only):
    """Evaluate model answers against ground truth."""
    conditions = ALL_CONDITIONS if condition == "all" else [condition]

    if compare_only:
        generate_readme_all()
        return

    for cond in conditions:
        print("=" * 60)
        print(f"Answer Evaluator — condition: {cond}")
        print("=" * 60)

        # Discover models
        if models:
            model_dirs = [ANSWERS_DIR / m for m in models]
        else:
            model_dirs = sorted([
                d for d in ANSWERS_DIR.iterdir()
                if d.is_dir() and not d.name.startswith(".") and (d / cond).is_dir()
            ])

        if not model_dirs:
            print("No model directories found.")
            continue

        print(f"Models to evaluate: {len(model_dirs)}")
        for md in model_dirs:
            print(f"  {md.name}")
        print()

        # Evaluate each model
        for model_dir in model_dirs:
            if not model_dir.is_dir():
                print(f"  {model_dir.name}: directory not found, skipping")
                continue
            evaluate_model(model_dir, cond, force=force)

        # Print comparison leaderboard
        generate_comparison(cond)

    # Generate README with all analyses
    generate_readme_all()


if __name__ == "__main__":
    main()
