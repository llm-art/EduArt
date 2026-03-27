#!/usr/bin/env python3
"""
Ground-Truth Validation Script

Implements the two-stage validation protocol described in methodology.md §3:
  Stage 1 — Stratified random sampling of ≥15% Zanichelli items for manual review.
  Stage 2 — Cross-model re-extraction (gemini-2.5-flash-lite + gpt-4.1) with
             three-way disagreement analysis against the original extraction.

Usage:
    # Stage 1 only: generate the manual-review sample
    python validation.py sample --seed 42

    # Stage 2 only: re-extract with two models and compare
    python validation.py reextract --start 1 --end 57

    # Stage 2: compare existing re-extractions against originals
    python validation.py compare

    # Full pipeline
    python validation.py full --seed 42

    # Interactive manual review UI
    python validation.py review
"""

import base64
import click
import http.server
import json
import math
import os
import random
import re
import socketserver
import sys
import time
import threading
import webbrowser
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

# Add questions directory to path for shared modules
ZANICHELLI_DIR = Path(__file__).parent            # datasets/questions/myzanichelli/
QUESTIONS_DIR = ZANICHELLI_DIR.parent             # datasets/questions/
sys.path.insert(0, str(QUESTIONS_DIR))

from modules.llm.factory import create_llm_provider, LLMConfig
from modules.managers.prompt_manager import PromptManager

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_DIR = QUESTIONS_DIR.parent                   # datasets/
RAW_DIR = ZANICHELLI_DIR / "raw"
STRUCTURED_DIR = ZANICHELLI_DIR / "structured"
PROMPTS_DIR = BASE_DIR / "prompts"
VALIDATION_DIR = BASE_DIR / "validation"

SAMPLE_FRACTION = 0.15          # ≥15 % of Zanichelli items
REEXTRACTOR_A = ("google", "gemini-2.5-flash-lite")
REEXTRACTOR_B = ("harvard", "us.anthropic.claude-haiku-4-5-20251001-v1:0")

# Fields compared in the three-way alignment
COMPARED_FIELDS = ["question_title", "instructions", "question_text", "choices", "answers", "type"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_structured_json(exercise: int, question: int, label: Optional[str] = None) -> Optional[Dict]:
    """
    Load a structured JSON for a given exercise/question.

    Args:
        exercise: Exercise number
        question: Question number
        label: If None, loads the original. Otherwise loads the re-extraction
               stored as {question}.{label}.json
    """
    if label:
        path = STRUCTURED_DIR / str(exercise) / "json" / f"{question}.{label}.json"
    else:
        path = STRUCTURED_DIR / str(exercise) / "json" / f"{question}.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_any_model_json(exercise: int, question: int) -> Optional[Dict]:
    """Load the first model-specific JSON found for a question."""
    json_dir = STRUCTURED_DIR / str(exercise) / "json"
    if not json_dir.exists():
        return None
    for f in sorted(json_dir.glob(f"{question}.*.json")):
        # Ensure it's a model file, not something else
        label = f.stem.split(".", 1)[1] if "." in f.stem else None
        if label:
            return json.load(open(f, encoding="utf-8"))
    return None


def compare_two_models(field: str, data_a, data_b) -> Dict:
    """
    Compare a single field across two model extractions.
    Returns {status: 'agreed'|'disagreed', ...}.
    """
    def get_val(data, f):
        if not data:
            return None
        return data.get(f)

    va = get_val(data_a, field)
    vb = get_val(data_b, field)

    if field in ("question_text", "question_title", "instructions"):
        na, nb = _normalise_text(va), _normalise_text(vb)
    elif field == "choices":
        na, nb = _normalise_choices(va), _normalise_choices(vb)
    elif field == "answers":
        na, nb = _normalise_answers(va), _normalise_answers(vb)
    elif field == "type":
        na = _normalise_text(str(va)) if va else ""
        nb = _normalise_text(str(vb)) if vb else ""
    else:
        na, nb = va, vb

    if na == nb:
        return {"status": "agreed", "value": va}
    else:
        return {"status": "disagreed", "value_a": va, "value_b": vb}


def enumerate_zanichelli_questions() -> List[Dict]:
    """
    Walk the structured/ tree and return ALL questions:
      - merged {q}.json (agreed or manually resolved)
      - unmerged {q}.{model}.json pairs (need review)

    Returns list of dicts:
      { exercise, question, type, has_image, path, merged, model_files }
    """
    # Collect all json files per (exercise, question)
    ex_q_files: Dict[tuple, Dict] = {}  # (ex, qn) -> {"merged": path, "models": {label: path}}

    for exercise_dir in sorted(STRUCTURED_DIR.iterdir()):
        if not exercise_dir.is_dir():
            continue
        try:
            exercise = int(exercise_dir.name)
        except ValueError:
            continue
        json_dir = exercise_dir / "json"
        if not json_dir.exists():
            continue
        for json_file in sorted(json_dir.glob("*.json")):
            stem = json_file.stem
            if stem.isdigit():
                # Merged file: {q}.json
                qn = int(stem)
                key = (exercise, qn)
                if key not in ex_q_files:
                    ex_q_files[key] = {"merged": None, "models": {}}
                ex_q_files[key]["merged"] = json_file
            else:
                # Model file: {q}.{model_label}.json
                parts = stem.split(".", 1)
                if len(parts) == 2 and parts[0].isdigit():
                    qn = int(parts[0])
                    label = parts[1]
                    key = (exercise, qn)
                    if key not in ex_q_files:
                        ex_q_files[key] = {"merged": None, "models": {}}
                    ex_q_files[key]["models"][label] = json_file

    items = []
    for (exercise, question), files in sorted(ex_q_files.items()):
        merged = files["merged"]
        model_files = files["models"]

        # Use merged file if available, otherwise pick first model file for metadata
        if merged:
            data = json.loads(merged.read_text(encoding="utf-8"))
            path = str(merged)
        elif model_files:
            first_model = next(iter(model_files.values()))
            data = json.loads(first_model.read_text(encoding="utf-8"))
            path = str(first_model)
        else:
            continue

        items.append({
            "exercise": exercise,
            "question": question,
            "type": data.get("type", "unknown"),
            "has_image": data.get("has_image", False),
            "path": path,
            "merged": merged is not None,
            "model_files": {label: str(p) for label, p in model_files.items()},
        })
    return items


def screenshot_path(exercise: int, question: int) -> Optional[Path]:
    """Return the screenshot path for a Zanichelli question, or None."""
    p = RAW_DIR / str(exercise) / "screenshot" / f"{question}.png"
    return p if p.exists() else None


def ocr_text_for(exercise: int, question: int) -> str:
    """Read the OCR text file for a question."""
    p = RAW_DIR / str(exercise) / "txt" / f"{question}.txt"
    if p.exists():
        return p.read_text(encoding="utf-8", errors="replace")
    return ""


def html_text_for(exercise: int, question: int) -> str:
    """Read the HTML file for a question."""
    p = RAW_DIR / str(exercise) / "html" / f"{question}.html"
    if p.exists():
        return p.read_text(encoding="utf-8", errors="replace")
    return ""


# ---------------------------------------------------------------------------
# Stage 1: Stratified Sampling
# ---------------------------------------------------------------------------

def stratified_sample(items: List[Dict], fraction: float, seed: int) -> List[Dict]:
    """
    Draw a stratified random sample from *items*.

    Strata:
      1. question type  (7 levels)
      2. exercise tercile  (3 levels: 1-19, 20-38, 39-57)
      3. has_image  (2 levels)

    Within each stratum cell at least ``ceil(n * fraction)`` items are drawn,
    so the total sample is ≥ fraction of the corpus.
    """
    rng = random.Random(seed)

    def tercile(exercise: int) -> int:
        if exercise <= 19:
            return 1
        elif exercise <= 38:
            return 2
        return 3

    # Bin items into strata
    strata: Dict[Tuple, List[Dict]] = defaultdict(list)
    for item in items:
        key = (item["type"], tercile(item["exercise"]), item["has_image"])
        strata[key].append(item)

    sample = []
    for key, members in strata.items():
        n = max(1, math.ceil(len(members) * fraction))
        n = min(n, len(members))
        sample.extend(rng.sample(members, n))

    return sample


def write_sample_report(sample: List[Dict], all_items: List[Dict], seed: int) -> Path:
    """Write a review checklist for the sampled questions."""
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    report_path = VALIDATION_DIR / "stage1_sample.json"
    readme_path = VALIDATION_DIR / "stage1_review_checklist.md"

    # Summary stats
    type_counts = defaultdict(int)
    for item in sample:
        type_counts[item["type"]] += 1

    report = {
        "generated": datetime.now().isoformat(),
        "seed": seed,
        "corpus_size": len(all_items),
        "sample_size": len(sample),
        "sample_fraction": round(len(sample) / len(all_items), 4),
        "strata_counts_by_type": dict(type_counts),
        "questions": [
            {
                "exercise": q["exercise"],
                "question": q["question"],
                "type": q["type"],
                "has_image": q["has_image"],
                "screenshot": str(screenshot_path(q["exercise"], q["question"]) or ""),
                "structured_json": q["path"],
            }
            for q in sorted(sample, key=lambda x: (x["exercise"], x["question"]))
        ],
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Markdown checklist
    lines = [
        "# Stage 1 — Manual Review Checklist",
        "",
        f"Generated: {report['generated']}",
        f"Seed: {seed}",
        f"Sample: {report['sample_size']} / {report['corpus_size']} "
        f"({report['sample_fraction']:.1%})",
        "",
        "## Instructions",
        "",
        "For each question below, open the screenshot and the structured JSON side-by-side.",
        "Compare field-by-field and record your verdict.",
        "",
        "| Verdict | Meaning |",
        "|---------|---------|",
        "| OK | All fields correct |",
        "| MINOR | Cosmetic issue (trailing punctuation, whitespace) — does not affect evaluation |",
        "| CRITICAL | Wrong answer key, missing choice, wrong type — affects evaluation |",
        "",
        "## Checklist",
        "",
        "| # | Exercise | Question | Type | Image | Verdict | Notes |",
        "|---|----------|----------|------|-------|---------|-------|",
    ]

    for i, q in enumerate(
        sorted(sample, key=lambda x: (x["exercise"], x["question"])), 1
    ):
        img = "yes" if q["has_image"] else "no"
        lines.append(
            f"| {i} | {q['exercise']} | {q['question']} | "
            f"`{q['type']}` | {img} | | |"
        )

    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total reviewed | |")
    lines.append(f"| OK | |")
    lines.append(f"| Minor errors | |")
    lines.append(f"| Critical errors | |")
    lines.append(f"| Critical-error rate | |")
    lines.append("")

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return report_path


# ---------------------------------------------------------------------------
# Stage 2: Cross-Model Re-Extraction
# ---------------------------------------------------------------------------

def _parse_json_response(text: str) -> Dict:
    """Best-effort parse of an LLM JSON response."""
    if isinstance(text, list):
        text = text[0] if text else ""
    if not text or text.strip() == "":
        return {}
    # Strip markdown fences
    text = re.sub(r"^(?:```(?:json)?\s*)", "", text)
    text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract the first JSON object
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return {}


def _retry_with_backoff(fn, max_retries=3, base_delay=1.0):
    """Call *fn*; on failure retry with exponential back-off."""
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            print(f"  Retry {attempt + 1}/{max_retries} after {delay}s — {e}")
            time.sleep(delay)


def reextract_question(
    provider,
    prompt_manager: PromptManager,
    exercise: int,
    question: int,
    question_type: str,
) -> Dict:
    """
    Re-extract a single question using *provider*.

    Returns the parsed JSON dict (or empty dict on failure), plus token metadata.
    """
    img = screenshot_path(exercise, question)
    if img is None:
        return {"error": "screenshot_missing"}

    ocr = ocr_text_for(exercise, question)
    html = html_text_for(exercise, question)

    # Map detailed type back to prompt key
    prompt_type = question_type
    if question_type in ("multiple_choice_radio", "multiple_choice_check"):
        prompt_type = "multiple_choice"

    system_prompt = prompt_manager.get_system_prompt()
    user_prompt = prompt_manager.get_text_extraction_prompt(
        question_type=prompt_type,
        ocr_text=ocr,
        html_text=html,
    )

    def _call():
        return provider.query(
            prompt=user_prompt,
            system_prompt=system_prompt,
            image_path=str(img),
        )

    response_text, token_meta = _retry_with_backoff(_call)
    parsed = _parse_json_response(response_text)
    parsed["_token_metadata"] = token_meta
    return parsed


def _reextraction_path(exercise: int, question: int, label: str) -> Path:
    """Return the path for a re-extraction file inside the structured/ tree."""
    return STRUCTURED_DIR / str(exercise) / "json" / f"{question}.{label}.json"


def discover_reextraction_labels() -> List[str]:
    """Scan the structured/ tree and return all re-extraction model labels found."""
    labels = set()
    for exercise_dir in STRUCTURED_DIR.iterdir():
        if not exercise_dir.is_dir():
            continue
        json_dir = exercise_dir / "json"
        if not json_dir.exists():
            continue
        for f in json_dir.iterdir():
            # Original files: 1.json, 2.json
            # Re-extractions: 1.google_gemini-2.5-flash-lite.json
            parts = f.stem.split(".", 1)
            if len(parts) == 2 and parts[0].isdigit():
                labels.add(parts[1])
    return sorted(labels)


def run_reextraction(
    exercises: Optional[Tuple[int, int]] = None,
    models: Optional[List[str]] = None,
    keep_amended: bool = False,
    force: bool = False,
) -> Path:
    """
    Run Stage 2 re-extraction over Zanichelli questions.

    Stores results alongside originals in structured/{exercise}/json/{question}.{label}.json
    """
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    # Determine which re-extractor models to use
    if models:
        model_specs = []
        for m in models:
            if "/" in m:
                provider_type, model_name = m.split("/", 1)
            else:
                provider_type, model_name = "google", m
            model_specs.append((provider_type, model_name))
    else:
        model_specs = [REEXTRACTOR_A, REEXTRACTOR_B]

    prompt_manager = PromptManager(prompts_dir=PROMPTS_DIR)

    # Initialise providers
    providers = {}
    for provider_type, model_name in model_specs:
        label = f"{provider_type}_{model_name}".replace("/", "_")
        try:
            provider = create_llm_provider(provider_type, model_name, max_tokens=2048)
            providers[label] = provider
            print(f"Initialized {label}")
        except Exception as e:
            print(f"WARNING: Could not initialise {label}: {e}")

    if not providers:
        print("ERROR: No re-extractor providers available. Check API keys.")
        sys.exit(1)

    # Enumerate questions
    all_items = enumerate_zanichelli_questions()
    if exercises:
        start_ex, end_ex = exercises
        all_items = [q for q in all_items if start_ex <= q["exercise"] <= end_ex]

    # Skip already-amended questions if requested
    if keep_amended:
        amendments = _load_amendments()
        before = len(all_items)
        all_items = [q for q in all_items
                     if f"{q['exercise']}_{q['question']}" not in amendments]
        print(f"Skipping {before - len(all_items)} amended questions (--keep-amend)")

    total = len(all_items)
    print(f"\nRe-extracting {total} questions with {len(providers)} model(s)...")

    total_tokens = defaultdict(lambda: {"input": 0, "output": 0})

    for idx, item in enumerate(all_items, 1):
        ex, qn, qtype = item["exercise"], item["question"], item["type"]
        print(f"[{idx}/{total}] exercise={ex} question={qn} type={qtype}")

        for label, provider in providers.items():
            out_file = _reextraction_path(ex, qn, label)

            # Skip if already extracted (unless --force)
            if out_file.exists() and not force:
                print(f"  {label}: skip (exists)")
                continue
            if out_file.exists() and force:
                out_file.unlink()

            try:
                result = reextract_question(
                    provider, prompt_manager, ex, qn, qtype
                )
                tokens = result.pop("_token_metadata", {})
                total_tokens[label]["input"] += tokens.get("input_tokens", 0)
                total_tokens[label]["output"] += tokens.get("output_tokens", 0)

                # Store in the same format as the original structured JSON,
                # with extra metadata fields for traceability
                output = dict(result)
                output["exercise"] = ex
                output["question"] = qn
                output["_reextraction"] = {
                    "model": label,
                    "original_type": qtype,
                    "token_metadata": tokens,
                    "timestamp": datetime.now().isoformat(),
                }
                out_file.parent.mkdir(parents=True, exist_ok=True)
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(output, f, indent=2, ensure_ascii=False)
                print(f"  {label}: OK")

            except Exception as e:
                print(f"  {label}: FAILED — {e}")

            # Rate-limit courtesy pause
            time.sleep(0.5)

    # Write token summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "questions_processed": total,
        "token_usage": {k: dict(v) for k, v in total_tokens.items()},
    }
    summary_path = VALIDATION_DIR / "reextraction_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nToken summary written to {summary_path}")

    return STRUCTURED_DIR


# ---------------------------------------------------------------------------
# Stage 2b: Three-Way Comparison
# ---------------------------------------------------------------------------

def _normalise_text(s: Optional[str]) -> str:
    """Lower-case, collapse whitespace, strip punctuation for fuzzy compare."""
    if not s:
        return ""
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[.,;:!?]+$", "", s)
    return s


def _normalise_choices(choices) -> List[Tuple[str, str]]:
    """Turn choices list into sorted (id, text) pairs for comparison."""
    if not choices:
        return []
    result = []
    for c in choices:
        if isinstance(c, dict):
            cid = str(c.get("id", "")).strip().upper()
            ctxt = _normalise_text(c.get("text", ""))
            result.append((cid, ctxt))
    return sorted(result)


def _normalise_answers(answers) -> List[Tuple[str, str]]:
    """Turn answers into sorted (id, description) pairs."""
    if not answers:
        return []
    result = []
    for a in answers:
        if isinstance(a, dict):
            aid = str(a.get("id", "")).strip().upper()
            adesc = _normalise_text(a.get("description", a.get("text", "")))
            result.append((aid, adesc))
        elif isinstance(a, str):
            result.append(("", _normalise_text(a)))
    return sorted(result)


def compare_field(field: str, original, reextracted_a, reextracted_b) -> Dict:
    """
    Compare a single field across three extractions.

    Returns a dict with 'status' in {unanimous, majority, no_majority}
    and detail about which extraction(s) disagree.
    """
    def get_val(data, field):
        if not data:
            return None
        return data.get(field)

    vo = get_val(original, field)
    va = get_val(reextracted_a, field)
    vb = get_val(reextracted_b, field)

    # Normalise for comparison
    if field == "question_text":
        no, na, nb = _normalise_text(vo), _normalise_text(va), _normalise_text(vb)
    elif field == "choices":
        no, na, nb = _normalise_choices(vo), _normalise_choices(va), _normalise_choices(vb)
    elif field == "answers":
        no, na, nb = _normalise_answers(vo), _normalise_answers(va), _normalise_answers(vb)
    elif field == "type":
        no = _normalise_text(str(vo)) if vo else ""
        na = _normalise_text(str(va)) if va else ""
        nb = _normalise_text(str(vb)) if vb else ""
    else:
        no, na, nb = vo, va, vb

    if no == na == nb:
        return {"status": "unanimous"}

    # Check pairwise agreement
    if no == na:
        return {
            "status": "majority",
            "majority_value": vo,
            "dissenter": "reextractor_b",
            "dissenter_value": vb,
        }
    if no == nb:
        return {
            "status": "majority",
            "majority_value": vo,
            "dissenter": "reextractor_a",
            "dissenter_value": va,
        }
    if na == nb:
        return {
            "status": "majority",
            "majority_value": va,
            "dissenter": "original",
            "dissenter_value": vo,
        }

    return {
        "status": "no_majority",
        "original": vo,
        "reextractor_a": va,
        "reextractor_b": vb,
    }


def run_comparison() -> Path:
    """
    Perform three-way comparison between original extractions and re-extractions.

    Re-extractions are read from structured/{exercise}/json/{question}.{label}.json.

    Writes:
      - validation/stage2_disagreements.json  (all non-unanimous items)
      - validation/stage2_review_checklist.md  (for manual adjudication)
      - validation/stage2_summary.json         (aggregate statistics)
    """
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    # Discover available re-extractor labels from the structured/ tree
    labels = discover_reextraction_labels()
    if not labels:
        print("ERROR: No re-extractions found. Run 'reextract' first.")
        sys.exit(1)

    if len(labels) < 2:
        print(f"WARNING: Only {len(labels)} re-extractor(s) found; need 2 for three-way comparison.")

    label_a = labels[0]
    label_b = labels[1] if len(labels) >= 2 else None
    print(f"Re-extractor A: {label_a}")
    if label_b:
        print(f"Re-extractor B: {label_b}")

    # Enumerate all questions
    all_items = enumerate_zanichelli_questions()

    disagreements = []
    stats = {
        "total": 0,
        "unanimous": 0,
        "majority_agreement": 0,
        "no_majority": 0,
        "missing_reextraction": 0,
        "field_disagreements": defaultdict(int),
    }

    for item in all_items:
        ex, qn = item["exercise"], item["question"]
        stats["total"] += 1

        original = load_structured_json(ex, qn)
        if original is None:
            continue

        # Load re-extractions from the structured/ tree
        data_a = load_structured_json(ex, qn, label=label_a)
        data_b = load_structured_json(ex, qn, label=label_b) if label_b else None

        if data_a is None:
            stats["missing_reextraction"] += 1
            continue

        # Compare fields
        question_result = {
            "exercise": ex,
            "question": qn,
            "type": item["type"],
            "fields": {},
            "overall": "unanimous",
        }

        for field in COMPARED_FIELDS:
            cmp = compare_field(field, original, data_a, data_b)
            question_result["fields"][field] = cmp

            if cmp["status"] != "unanimous":
                stats["field_disagreements"][field] += 1
                if cmp["status"] == "no_majority":
                    question_result["overall"] = "no_majority"
                elif question_result["overall"] != "no_majority":
                    question_result["overall"] = "majority_agreement"

        if question_result["overall"] == "unanimous":
            stats["unanimous"] += 1
        elif question_result["overall"] == "majority_agreement":
            stats["majority_agreement"] += 1
            disagreements.append(question_result)
        else:
            stats["no_majority"] += 1
            disagreements.append(question_result)

    # Sort disagreements: no_majority first, then by exercise/question
    disagreements.sort(
        key=lambda d: (0 if d["overall"] == "no_majority" else 1, d["exercise"], d["question"])
    )

    # Write disagreements
    dis_path = VALIDATION_DIR / "stage2_disagreements.json"
    with open(dis_path, "w", encoding="utf-8") as f:
        json.dump(disagreements, f, indent=2, ensure_ascii=False)

    # Write summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "reextractor_a": label_a,
        "reextractor_b": label_b,
        "total_questions": stats["total"],
        "unanimous": stats["unanimous"],
        "majority_agreement": stats["majority_agreement"],
        "no_majority": stats["no_majority"],
        "missing_reextraction": stats["missing_reextraction"],
        "disagreement_rate": round(
            (stats["majority_agreement"] + stats["no_majority"]) / max(stats["total"], 1), 4
        ),
        "field_disagreements": dict(stats["field_disagreements"]),
    }
    sum_path = VALIDATION_DIR / "stage2_summary.json"
    with open(sum_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Write markdown checklist
    _write_comparison_checklist(disagreements, summary)

    print(f"\nComparison complete:")
    print(f"  Total questions:      {stats['total']}")
    print(f"  Unanimous:            {stats['unanimous']}")
    print(f"  Majority agreement:   {stats['majority_agreement']}")
    print(f"  No majority:          {stats['no_majority']}")
    print(f"  Disagreement rate:    {summary['disagreement_rate']:.1%}")
    print(f"\nDisagreements written to {dis_path}")

    return dis_path


def _write_comparison_checklist(disagreements: List[Dict], summary: Dict):
    """Write a Markdown checklist for human adjudication of disagreements."""
    path = VALIDATION_DIR / "stage2_review_checklist.md"
    lines = [
        "# Stage 2 — Disagreement Adjudication Checklist",
        "",
        f"Generated: {summary['timestamp']}",
        f"Re-extractor A: `{summary['reextractor_a']}`",
        f"Re-extractor B: `{summary.get('reextractor_b', 'N/A')}`",
        "",
        f"Total disagreements: **{len(disagreements)}** "
        f"(of {summary['total_questions']} questions, "
        f"{summary['disagreement_rate']:.1%})",
        "",
        "## Priority: No-Majority Items (all three extractions differ)",
        "",
        "| # | Exercise | Question | Type | Disagreeing Fields | Verdict | Corrected Value |",
        "|---|----------|----------|------|--------------------|---------|-----------------|",
    ]

    idx = 0
    for d in disagreements:
        if d["overall"] != "no_majority":
            continue
        idx += 1
        fields = ", ".join(
            f for f, v in d["fields"].items() if v["status"] != "unanimous"
        )
        lines.append(
            f"| {idx} | {d['exercise']} | {d['question']} | "
            f"`{d['type']}` | {fields} | | |"
        )

    lines.extend([
        "",
        "## Majority-Agreement Items (two of three agree; one dissents)",
        "",
        "| # | Exercise | Question | Type | Field | Dissenter | Verdict | Corrected Value |",
        "|---|----------|----------|------|-------|-----------|---------|-----------------|",
    ])

    idx = 0
    for d in disagreements:
        if d["overall"] != "majority_agreement":
            continue
        for field, cmp in d["fields"].items():
            if cmp["status"] == "unanimous":
                continue
            idx += 1
            dissenter = cmp.get("dissenter", "?")
            lines.append(
                f"| {idx} | {d['exercise']} | {d['question']} | "
                f"`{d['type']}` | {field} | {dissenter} | | |"
            )

    lines.extend([
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        "| Total adjudicated | |",
        "| Original was correct | |",
        "| Original had error (corrected) | |",
        "| Critical corrections applied | |",
        "",
    ])

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Stage 1b: Interactive Review Server
# ---------------------------------------------------------------------------

REVIEW_VERDICTS_FILE = VALIDATION_DIR / "stage1_verdicts.json"


def _load_verdicts() -> Dict[str, Dict]:
    """Load existing review verdicts."""
    if REVIEW_VERDICTS_FILE.exists():
        return json.loads(REVIEW_VERDICTS_FILE.read_text(encoding="utf-8"))
    return {}


def _save_verdicts(verdicts: Dict[str, Dict]):
    """Persist review verdicts."""
    REVIEW_VERDICTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REVIEW_VERDICTS_FILE, "w", encoding="utf-8") as f:
        json.dump(verdicts, f, indent=2, ensure_ascii=False)


def _image_to_data_uri(path: Path) -> str:
    """Convert an image file to a data: URI for embedding in HTML."""
    if not path or not path.exists():
        return ""
    suffix = path.suffix.lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "gif": "image/gif", "webp": "image/webp"}.get(suffix.lstrip("."), "image/png")
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{data}"


def _build_review_html(sample: List[Dict]) -> str:
    """Build the single-page review application."""
    # Pre-load all question data + images
    questions_js = []
    for item in sorted(sample, key=lambda x: (x["exercise"], x["question"])):
        ex, qn = item["exercise"], item["question"]
        structured = load_structured_json(ex, qn) or {}
        scrn = screenshot_path(ex, qn)
        screenshot_uri = _image_to_data_uri(scrn) if scrn else ""

        questions_js.append({
            "exercise": ex,
            "question": qn,
            "key": f"{ex}_{qn}",
            "type": item["type"],
            "has_image": item["has_image"],
            "screenshot": screenshot_uri,
            "json": structured,
        })

    verdicts = _load_verdicts()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Stage 1 — Manual Review</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #f5f5f5; color: #333; }}
  .header {{ background: #1a1a2e; color: #fff; padding: 12px 24px;
             display: flex; align-items: center; justify-content: space-between;
             position: sticky; top: 0; z-index: 100; }}
  .header h1 {{ font-size: 18px; font-weight: 600; }}
  .progress {{ font-size: 14px; opacity: 0.8; }}
  .nav {{ display: flex; gap: 8px; align-items: center; }}
  .nav button {{ background: #16213e; color: #fff; border: 1px solid #0f3460;
                 padding: 6px 16px; border-radius: 4px; cursor: pointer; font-size: 14px; }}
  .nav button:hover {{ background: #0f3460; }}
  .nav button:disabled {{ opacity: 0.4; cursor: default; }}
  .counter {{ font-size: 14px; min-width: 80px; text-align: center; }}
  .main {{ display: flex; height: calc(100vh - 52px); }}
  .screenshot-panel {{ flex: 1; overflow: auto; background: #222; padding: 8px;
                       display: flex; align-items: flex-start; justify-content: center; }}
  .screenshot-panel img {{ max-width: 100%; height: auto; }}
  .review-panel {{ width: 520px; overflow-y: auto; background: #fff;
                   border-left: 2px solid #ddd; padding: 16px; }}
  .meta {{ background: #f0f0f0; padding: 10px 14px; border-radius: 6px; margin-bottom: 12px;
           font-size: 13px; display: flex; gap: 16px; flex-wrap: wrap; }}
  .meta span {{ white-space: nowrap; }}
  .meta strong {{ color: #555; }}
  .field {{ margin-bottom: 14px; }}
  .field-label {{ font-size: 12px; font-weight: 600; color: #888; text-transform: uppercase;
                  margin-bottom: 4px; }}
  .field-value {{ background: #fafafa; border: 1px solid #e0e0e0; border-radius: 4px;
                  padding: 8px 10px; font-size: 13px; white-space: pre-wrap;
                  max-height: 200px; overflow-y: auto; font-family: monospace; }}
  .verdict-bar {{ position: sticky; bottom: 0; background: #fff;
                  border-top: 2px solid #eee; padding: 12px 0; display: flex;
                  gap: 8px; flex-wrap: wrap; align-items: center; }}
  .verdict-btn {{ padding: 8px 20px; border-radius: 6px; border: 2px solid transparent;
                  font-size: 14px; font-weight: 600; cursor: pointer; transition: 0.15s; }}
  .verdict-btn:hover {{ filter: brightness(1.1); }}
  .btn-ok {{ background: #d4edda; color: #155724; border-color: #c3e6cb; }}
  .btn-ok.active {{ background: #28a745; color: #fff; }}
  .btn-minor {{ background: #fff3cd; color: #856404; border-color: #ffeeba; }}
  .btn-minor.active {{ background: #ffc107; color: #333; }}
  .btn-critical {{ background: #f8d7da; color: #721c24; border-color: #f5c6cb; }}
  .btn-critical.active {{ background: #dc3545; color: #fff; }}
  .notes-input {{ width: 100%; margin-top: 8px; padding: 6px 10px; border: 1px solid #ccc;
                  border-radius: 4px; font-size: 13px; }}
  .sidebar {{ display: flex; flex-direction: column; }}
  .q-list {{ width: 60px; background: #eee; overflow-y: auto; height: calc(100vh - 52px); }}
  .q-item {{ padding: 6px 0; text-align: center; font-size: 12px; cursor: pointer;
             border-bottom: 1px solid #ddd; }}
  .q-item:hover {{ background: #ddd; }}
  .q-item.active {{ background: #1a1a2e; color: #fff; }}
  .q-item.ok {{ border-left: 4px solid #28a745; }}
  .q-item.minor {{ border-left: 4px solid #ffc107; }}
  .q-item.critical {{ border-left: 4px solid #dc3545; }}
  .summary-box {{ margin-top: 16px; background: #f0f0f0; padding: 12px; border-radius: 6px;
                  font-size: 13px; }}
  .no-screenshot {{ color: #999; font-style: italic; padding: 40px; }}
</style>
</head>
<body>

<div class="header">
  <h1>Stage 1 — Manual Review</h1>
  <span class="progress" id="progress"></span>
  <div class="nav">
    <button id="prevBtn" onclick="go(-1)">&larr; Prev</button>
    <span class="counter" id="counter"></span>
    <button id="nextBtn" onclick="go(1)">Next &rarr;</button>
    <button onclick="save()" style="background:#28a745;border-color:#28a745">Save</button>
  </div>
</div>

<div style="display:flex">
  <div class="q-list" id="qlist"></div>
  <div class="main">
    <div class="screenshot-panel" id="screenshotPanel">
      <img id="screenshotImg">
      <div class="no-screenshot" id="noScreenshot" style="display:none">No screenshot available</div>
    </div>
    <div class="review-panel" id="reviewPanel"></div>
  </div>
</div>

<script>
const QUESTIONS = {json.dumps(questions_js, ensure_ascii=False)};
let verdicts = {json.dumps(verdicts, ensure_ascii=False)};
let current = 0;

function renderList() {{
  const el = document.getElementById('qlist');
  el.innerHTML = QUESTIONS.map((q, i) => {{
    const v = verdicts[q.key];
    const cls = v ? v.verdict.toLowerCase() : '';
    const act = i === current ? ' active' : '';
    return `<div class="q-item ${{cls}}${{act}}" onclick="goTo(${{i}})" title="Ex${{q.exercise}} Q${{q.question}}">${{i+1}}</div>`;
  }}).join('');
}}

function render() {{
  const q = QUESTIONS[current];
  const v = verdicts[q.key] || {{}};

  // Counter
  document.getElementById('counter').textContent = `${{current+1}} / ${{QUESTIONS.length}}`;
  document.getElementById('prevBtn').disabled = current === 0;
  document.getElementById('nextBtn').disabled = current === QUESTIONS.length - 1;

  // Progress
  const done = Object.keys(verdicts).length;
  document.getElementById('progress').textContent =
    `${{done}} / ${{QUESTIONS.length}} reviewed (${{Math.round(done/QUESTIONS.length*100)}}%)`;

  // Screenshot
  const img = document.getElementById('screenshotImg');
  const noImg = document.getElementById('noScreenshot');
  if (q.screenshot) {{
    img.src = q.screenshot;
    img.style.display = 'block';
    noImg.style.display = 'none';
  }} else {{
    img.style.display = 'none';
    noImg.style.display = 'block';
  }}

  // JSON fields
  const j = q.json;
  let html = `
    <div class="meta">
      <span><strong>Exercise:</strong> ${{q.exercise}}</span>
      <span><strong>Question:</strong> ${{q.question}}</span>
      <span><strong>Type:</strong> ${{q.type}}</span>
      <span><strong>Image:</strong> ${{q.has_image ? 'yes' : 'no'}}</span>
    </div>
    <div class="field">
      <div class="field-label">question_text</div>
      <div class="field-value">${{esc(j.question_text || '')}}</div>
    </div>
    <div class="field">
      <div class="field-label">question_title</div>
      <div class="field-value">${{esc(j.question_title || '')}}</div>
    </div>
    <div class="field">
      <div class="field-label">choices</div>
      <div class="field-value">${{esc(JSON.stringify(j.choices || [], null, 2))}}</div>
    </div>
    <div class="field">
      <div class="field-label">answers (ground truth)</div>
      <div class="field-value">${{esc(JSON.stringify(j.answers || [], null, 2))}}</div>
    </div>
    <div class="field">
      <div class="field-label">type</div>
      <div class="field-value">${{esc(j.type || '')}}</div>
    </div>`;

  // Verdict bar
  const vv = v.verdict || '';
  html += `
    <div class="verdict-bar">
      <button class="verdict-btn btn-ok ${{vv==='OK'?'active':''}}" onclick="setVerdict('OK')">OK</button>
      <button class="verdict-btn btn-minor ${{vv==='MINOR'?'active':''}}" onclick="setVerdict('MINOR')">Minor</button>
      <button class="verdict-btn btn-critical ${{vv==='CRITICAL'?'active':''}}" onclick="setVerdict('CRITICAL')">Critical</button>
      <input class="notes-input" id="notesInput" placeholder="Notes (optional)..."
             value="${{esc(v.notes || '')}}" oninput="updateNotes(this.value)">
    </div>`;

  // Summary
  const counts = {{OK:0, MINOR:0, CRITICAL:0}};
  Object.values(verdicts).forEach(v => {{ if(counts[v.verdict]!==undefined) counts[v.verdict]++; }});
  html += `
    <div class="summary-box">
      <strong>Progress:</strong> ${{done}} / ${{QUESTIONS.length}}<br>
      OK: ${{counts.OK}} &nbsp; Minor: ${{counts.MINOR}} &nbsp; Critical: ${{counts.CRITICAL}}
      ${{QUESTIONS.length === done ? '<br><strong>Review complete!</strong>' : ''}}
    </div>`;

  document.getElementById('reviewPanel').innerHTML = html;
  renderList();
}}

function esc(s) {{
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}}

function setVerdict(v) {{
  const q = QUESTIONS[current];
  const existing = verdicts[q.key] || {{}};
  verdicts[q.key] = {{
    exercise: q.exercise, question: q.question, type: q.type,
    verdict: v, notes: existing.notes || '',
    timestamp: new Date().toISOString()
  }};
  render();
  // Auto-save
  save();
  // Auto-advance to next unreviewed
  if (current < QUESTIONS.length - 1) {{
    setTimeout(() => go(1), 150);
  }}
}}

function updateNotes(n) {{
  const q = QUESTIONS[current];
  if (!verdicts[q.key]) {{
    verdicts[q.key] = {{
      exercise: q.exercise, question: q.question, type: q.type,
      verdict: '', notes: '', timestamp: new Date().toISOString()
    }};
  }}
  verdicts[q.key].notes = n;
  save();
}}

function go(delta) {{
  current = Math.max(0, Math.min(QUESTIONS.length - 1, current + delta));
  render();
}}

function goTo(i) {{
  current = i;
  render();
}}

function save() {{
  fetch('/save', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify(verdicts)
  }}).then(r => r.json()).then(d => {{
    if (!d.ok) console.error('Save failed');
  }});
}}

// Keyboard navigation
document.addEventListener('keydown', e => {{
  if (e.target.tagName === 'INPUT') return;
  if (e.key === 'ArrowLeft' || e.key === 'a') go(-1);
  if (e.key === 'ArrowRight' || e.key === 'd') go(1);
  if (e.key === '1') setVerdict('OK');
  if (e.key === '2') setVerdict('MINOR');
  if (e.key === '3') setVerdict('CRITICAL');
}});

render();
</script>
</body>
</html>"""


class ReviewHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler for the review UI."""

    html_content = ""  # Set by run_review_server

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(self.html_content.encode("utf-8"))

    def do_POST(self):
        if self.path == "/save":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                verdicts = json.loads(body)
                _save_verdicts(verdicts)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Silence request logs


def run_review_server(port: int = 8899):
    """Launch the interactive review UI."""
    sample_path = VALIDATION_DIR / "stage1_sample.json"
    if not sample_path.exists():
        print("ERROR: No sample found. Run 'sample' first.")
        sys.exit(1)

    sample_data = json.loads(sample_path.read_text(encoding="utf-8"))
    sample = sample_data["questions"]
    print(f"Loading {len(sample)} questions for review...")

    ReviewHandler.html_content = _build_review_html(sample)

    with socketserver.TCPServer(("", port), ReviewHandler) as httpd:
        url = f"http://localhost:{port}"
        print(f"\nReview UI running at {url}")
        print("Keyboard shortcuts: 1=OK  2=Minor  3=Critical  Arrow keys=navigate")
        print("Press Ctrl+C to stop.\n")
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nReview server stopped.")
            verdicts = _load_verdicts()
            total = len(sample)
            done = len(verdicts)
            print(f"Reviewed {done}/{total} questions.")
            if verdicts:
                counts = defaultdict(int)
                for v in verdicts.values():
                    counts[v.get("verdict", "?")] += 1
                for k, c in sorted(counts.items()):
                    print(f"  {k}: {c}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.command()
@click.option("--port", type=int, default=8900, help="Port for the viewer server")
def cli(port):
    """Ground-truth validation viewer for the Art History dataset."""
    run_viewer_server(port=port)


# ---------------------------------------------------------------------------
# Viewer: comparison + inline editing UI
# ---------------------------------------------------------------------------

VIEWER_AMENDMENTS_FILE = VALIDATION_DIR / "viewer_amendments.json"


def _load_amendments() -> Dict:
    if VIEWER_AMENDMENTS_FILE.exists():
        return json.loads(VIEWER_AMENDMENTS_FILE.read_text(encoding="utf-8"))
    return {}


def _save_amendments(data: Dict):
    VIEWER_AMENDMENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(VIEWER_AMENDMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _build_viewer_html(questions_data: List[Dict]) -> str:
    """Build the viewer SPA with comparison + inline editing."""
    amendments = _load_amendments()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Ground Truth Viewer</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #f5f5f5; color: #333; font-size: 14px; }}
  .header {{ background: #1a1a2e; color: #fff; padding: 10px 20px;
             display: flex; align-items: center; justify-content: space-between;
             position: sticky; top: 0; z-index: 100; }}
  .header h1 {{ font-size: 16px; font-weight: 600; }}
  .nav {{ display: flex; gap: 6px; align-items: center; }}
  .nav button {{ background: #16213e; color: #fff; border: 1px solid #0f3460;
                 padding: 5px 14px; border-radius: 4px; cursor: pointer; font-size: 13px; }}
  .nav button:hover {{ background: #0f3460; }}
  .nav button:disabled {{ opacity: 0.4; cursor: default; }}
  .counter {{ font-size: 13px; min-width: 80px; text-align: center; color: #ccc; }}
  .filter-bar {{ background: #e8e8e8; padding: 6px 20px; display: flex; gap: 8px;
                 align-items: center; font-size: 13px; border-bottom: 1px solid #ccc; }}
  .filter-bar label {{ cursor: pointer; padding: 3px 10px; border-radius: 12px; }}
  .filter-bar label:hover {{ background: #ddd; }}
  .filter-bar input[type=radio] {{ display: none; }}
  .filter-bar input[type=radio]:checked + span {{ background: #1a1a2e; color: #fff;
                                                   padding: 3px 10px; border-radius: 12px; }}
  .filter-count {{ font-size: 11px; opacity: 0.7; }}
  .layout {{ display: flex; height: calc(100vh - 82px); }}
  .sidebar {{ width: 70px; background: #eee; overflow-y: auto; flex-shrink: 0; }}
  .q-item {{ padding: 5px 0; text-align: center; font-size: 11px; cursor: pointer;
             border-bottom: 1px solid #ddd; position: relative; }}
  .q-item:hover {{ background: #ddd; }}
  .q-item.active {{ background: #1a1a2e; color: #fff; }}
  .q-item.resolved {{ background: #d4edda; border-left: 4px solid #28a745; }}
  .q-item.resolved.active {{ background: #28a745; color: #fff; }}
  .q-item.needs-review {{ border-left: 4px solid #dc3545; }}
  .q-item.unanimous {{ border-left: 4px solid #28a745; }}
  .content {{ flex: 1; display: flex; overflow: hidden; }}
  .screenshot-panel {{ flex: 1; overflow: auto; background: #222; padding: 8px;
                       display: flex; align-items: flex-start; justify-content: center; }}
  .screenshot-panel img {{ max-width: 100%; height: auto; }}
  .spinner {{ color: #999; padding: 40px; text-align: center; font-style: italic; }}
  @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  .spinner::before {{ content: ''; display: inline-block; width: 20px; height: 20px;
    border: 2px solid #666; border-top-color: transparent; border-radius: 50%;
    animation: spin 0.8s linear infinite; margin-right: 8px; vertical-align: middle; }}
  .detail-panel {{ width: 640px; overflow-y: auto; background: #fff;
                   border-left: 2px solid #ddd; padding: 0; }}
  .meta {{ background: #f0f0f0; padding: 8px 12px; font-size: 12px;
           display: flex; gap: 14px; flex-wrap: wrap; align-items: center; }}
  .meta strong {{ color: #555; }}
  .status-badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px;
                   font-size: 11px; font-weight: 600; }}
  .status-unanimous {{ background: #d4edda; color: #155724; }}
  .status-majority {{ background: #fff3cd; color: #856404; }}
  .status-no_majority {{ background: #f8d7da; color: #721c24; }}
  .status-resolved {{ background: #28a745; color: #fff; }}
  /* Tabs */
  .tabs {{ display: flex; border-bottom: 2px solid #ddd; background: #fafafa;
           position: sticky; top: 0; z-index: 10; }}
  .tab {{ padding: 8px 16px; font-size: 13px; font-weight: 600; cursor: pointer;
          border-bottom: 3px solid transparent; margin-bottom: -2px; position: relative;
          color: #666; transition: 0.15s; white-space: nowrap; }}
  .tab:hover {{ color: #333; background: #f0f0f0; }}
  .tab.active {{ color: #1a1a2e; border-bottom-color: #1a1a2e; }}
  .tab.has-issue {{ color: #dc3545; }}
  .tab.has-issue.active {{ border-bottom-color: #dc3545; }}
  .tab.is-resolved {{ color: #28a745; }}
  .tab .tab-dot {{ position: absolute; top: 4px; right: 4px; width: 8px; height: 8px;
                   border-radius: 50%; }}
  .tab .tab-dot.dot-red {{ background: #dc3545; }}
  .tab .tab-dot.dot-green {{ background: #28a745; }}
  .tab-content {{ padding: 12px; display: none; }}
  .tab-content.active {{ display: block; }}
  /* Source cards */
  .source-card {{ background: #fafafa; border: 1px solid #e0e0e0; border-radius: 6px;
                  margin-bottom: 8px; overflow: hidden; }}
  .source-card-header {{ padding: 6px 10px; font-size: 11px; font-weight: 600;
                         text-transform: uppercase; color: #666; display: flex;
                         justify-content: space-between; align-items: center;
                         background: #f0f0f0; border-bottom: 1px solid #e0e0e0; }}
  .source-card-body {{ padding: 8px 10px; font-size: 12px; white-space: pre-wrap;
                       max-height: 220px; overflow-y: auto; font-family: monospace; }}
  .source-card.dissenter {{ border-color: #f5c6cb; }}
  .source-card.dissenter .source-card-header {{ background: #fff0f0; }}
  .source-card.majority-winner {{ border-color: #c3e6cb; }}
  .source-card.majority-winner .source-card-header {{ background: #f0fff0; }}
  .source-card.selected {{ border-color: #007bff; border-width: 2px; }}
  .source-card.selected .source-card-header {{ background: #e0f0ff; color: #007bff; }}
  .btn-select {{ background: #007bff; color: #fff; border: none; padding: 3px 12px;
                 border-radius: 4px; font-size: 11px; font-weight: 600; cursor: pointer; }}
  .btn-select:hover {{ background: #0069d9; }}
  .btn-select.btn-selected {{ background: #28a745; }}
  .btn-copy-edit {{ background: #6c757d; color: #fff; border: none; padding: 3px 12px;
                    border-radius: 4px; font-size: 11px; font-weight: 600; cursor: pointer;
                    margin-left: 4px; }}
  .btn-copy-edit:hover {{ background: #545b62; }}
  /* Edit area */
  .edit-section {{ border-top: 1px solid #e0e0e0; padding-top: 8px; margin-top: 8px; }}
  .edit-area {{ width: 100%; min-height: 80px; padding: 6px 8px; font-size: 12px;
                font-family: monospace; border: 2px solid #007bff; border-radius: 3px;
                background: #f0f8ff; resize: vertical; overflow: hidden; }}
  .btn-row {{ display: flex; gap: 6px; margin-top: 6px; flex-wrap: wrap; }}
  .btn-sm {{ padding: 4px 12px; border-radius: 4px; border: 1px solid #ccc;
             font-size: 12px; cursor: pointer; }}
  .btn-sm:hover {{ filter: brightness(0.95); }}
  .btn-save {{ background: #28a745; color: #fff; border-color: #28a745; }}
  .btn-revert {{ background: #dc3545; color: #fff; border-color: #dc3545; }}
  /* Mark correct button */
  .btn-mark-correct {{ background: #28a745; color: #fff; border: none; padding: 10px 20px;
                       border-radius: 6px; font-size: 14px; font-weight: 700; cursor: pointer;
                       width: 100%; margin: 10px 0; }}
  .btn-mark-correct:hover {{ background: #218838; }}
  .btn-accept-all {{ background: #ffc107; color: #333; border: none; padding: 10px 20px;
                     border-radius: 6px; font-size: 14px; font-weight: 700; cursor: pointer;
                     width: 100%; margin-bottom: 6px; }}
  .btn-accept-all:hover {{ background: #e0a800; }}
  .no-screenshot {{ color: #999; font-style: italic; padding: 40px; }}
  .toast {{ position: fixed; bottom: 20px; right: 20px; background: #28a745; color: #fff;
            padding: 10px 20px; border-radius: 6px; font-size: 13px; display: none;
            z-index: 200; }}
  ins {{ background: #acf2bd; text-decoration: none; padding: 1px 2px; border-radius: 2px; }}
  del {{ background: #fdb8c0; text-decoration: line-through; padding: 1px 2px; border-radius: 2px;
         opacity: 0.7; }}
  .resolved-banner {{ background: #d4edda; color: #155724; padding: 10px 14px; text-align: center;
                      font-weight: 700; font-size: 14px; border-bottom: 2px solid #c3e6cb; }}
</style>
</head>
<body>

<div class="header">
  <h1>Ground Truth Viewer</h1>
  <div class="nav">
    <button onclick="go(-1)" id="prevBtn">&larr; Prev</button>
    <span class="counter" id="counter"></span>
    <button onclick="go(1)" id="nextBtn">Next &rarr;</button>
    <button onclick="jumpToNextIssue()" style="background:#dc3545;border-color:#dc3545">
      Next Issue</button>
  </div>
</div>
<div class="filter-bar">
  <strong>Filter:</strong>
  <label><input type="radio" name="filter" value="all" checked onchange="applyFilter(this.value)">
    <span>All <span id="cnt_all" class="filter-count"></span></span></label>
  <label><input type="radio" name="filter" value="to_check" onchange="applyFilter(this.value)">
    <span>To Check <span id="cnt_to_check" class="filter-count"></span></span></label>
  <label><input type="radio" name="filter" value="resolved" onchange="applyFilter(this.value)">
    <span>Resolved <span id="cnt_resolved" class="filter-count"></span></span></label>
  <label><input type="radio" name="filter" value="unanimous" onchange="applyFilter(this.value)">
    <span>Unanimous <span id="cnt_unanimous" class="filter-count"></span></span></label>
</div>

<div class="layout">
  <div class="sidebar" id="sidebar"></div>
  <div class="content">
    <div class="screenshot-panel" id="screenshotPanel">
      <div id="imgSpinner" class="spinner" style="display:none">Loading...</div>
      <img id="screenshotImg" style="display:none">
      <div class="no-screenshot" id="noScreenshot" style="display:none">No screenshot</div>
    </div>
    <div class="detail-panel" id="detailPanel"></div>
  </div>
</div>
<div class="toast" id="toast">Saved</div>

<script>
const ALL_QUESTIONS = {json.dumps(questions_data, ensure_ascii=False)};
let amendments = {json.dumps(amendments, ensure_ascii=False)};
let filtered = [...ALL_QUESTIONS];
let current = 0;
let currentFilter = 'all';
let activeTab = 'question_text';

const FIELDS = ['question_title', 'instructions', 'question_text', 'choices', 'answers', 'type'];
const FIELD_LABELS = {{ question_title: 'Title', instructions: 'Instructions', question_text: 'Text', choices: 'Choices', answers: 'Answers', type: 'Type' }};

// Load latest amendments from server on startup (overrides baked-in snapshot)
fetch('/amendments').then(r => r.json()).then(data => {{
  amendments = data;
  applyFilter(currentFilter);
}}).catch(() => {{
  applyFilter(currentFilter);
}});

// A question is "resolved" if all disagreement fields have been amended
function isResolved(q) {{
  const cmp = q.comparison || {{}};
  if (cmp.overall === 'unanimous') return true;
  const am = amendments[q.key] || {{}};
  const fields = cmp.fields || {{}};
  for (const f of FIELDS) {{
    if (fields[f] && fields[f].status !== 'unanimous' && am[f] === undefined) return false;
  }}
  return Object.keys(am).length > 0;
}}

function needsReview(q) {{
  const cmp = q.comparison || {{}};
  if (cmp.overall === 'unanimous') return false;
  return !isResolved(q);
}}

function updateFilterCounts() {{
  const cAll = ALL_QUESTIONS.length;
  const cCheck = ALL_QUESTIONS.filter(q => needsReview(q)).length;
  const cResolved = ALL_QUESTIONS.filter(q => isResolved(q) && (q.comparison||{{}}).overall !== 'unanimous').length;
  const cUnanimous = ALL_QUESTIONS.filter(q => (q.comparison||{{}}).overall === 'unanimous').length;
  document.getElementById('cnt_all').textContent = '(' + cAll + ')';
  document.getElementById('cnt_to_check').textContent = '(' + cCheck + ')';
  document.getElementById('cnt_resolved').textContent = '(' + cResolved + ')';
  document.getElementById('cnt_unanimous').textContent = '(' + cUnanimous + ')';
}}

function applyFilter(f) {{
  currentFilter = f;
  if (f === 'all') {{
    filtered = [...ALL_QUESTIONS];
  }} else if (f === 'to_check') {{
    filtered = ALL_QUESTIONS.filter(q => needsReview(q));
  }} else if (f === 'resolved') {{
    filtered = ALL_QUESTIONS.filter(q => isResolved(q) && (q.comparison||{{}}).overall !== 'unanimous');
  }} else if (f === 'unanimous') {{
    filtered = ALL_QUESTIONS.filter(q => (q.comparison||{{}}).overall === 'unanimous');
  }}
  current = Math.min(current, Math.max(0, filtered.length - 1));
  updateFilterCounts();
  // Update filter radio
  document.querySelectorAll('.filter-bar input[type=radio]').forEach(r => r.checked = r.value === f);
  renderSidebar();
  render();
}}

function renderSidebar() {{
  const el = document.getElementById('sidebar');
  el.innerHTML = filtered.map((q, i) => {{
    const resolved = isResolved(q);
    const review = needsReview(q);
    const unanimous = (q.comparison||{{}}).overall === 'unanimous';
    let cls = '';
    if (resolved && !unanimous) cls = 'resolved';
    else if (review) cls = 'needs-review';
    else if (unanimous) cls = 'unanimous';
    const act = i === current ? ' active' : '';
    return `<div class="q-item ${{cls}}${{act}}" onclick="goTo(${{i}})" `
         + `title="Ex${{q.exercise}} Q${{q.question}}">`
         + `${{q.exercise}}/${{q.question}}</div>`;
  }}).join('');
}}

function switchTab(field) {{
  activeTab = field;
  render();
}}

function render() {{
  if (filtered.length === 0) {{
    document.getElementById('detailPanel').innerHTML = '<p style="padding:20px;color:#999">No questions match this filter.</p>';
    document.getElementById('screenshotImg').style.display = 'none';
    document.getElementById('noScreenshot').style.display = 'block';
    return;
  }}
  const q = filtered[current];
  const am = amendments[q.key] || {{}};

  document.getElementById('counter').textContent = `${{current+1}} / ${{filtered.length}}`;
  document.getElementById('prevBtn').disabled = current === 0;
  document.getElementById('nextBtn').disabled = current >= filtered.length - 1;

  // Screenshot with spinner
  const img = document.getElementById('screenshotImg');
  const noImg = document.getElementById('noScreenshot');
  const spinner = document.getElementById('imgSpinner');
  if (q.screenshot) {{
    img.style.display = 'none';
    noImg.style.display = 'none';
    spinner.style.display = 'block';
    const newImg = new Image();
    newImg.onload = function() {{
      img.src = newImg.src;
      img.style.display = 'block';
      spinner.style.display = 'none';
    }};
    newImg.onerror = function() {{
      spinner.style.display = 'none';
      noImg.style.display = 'block';
    }};
    newImg.src = q.screenshot;
  }} else {{
    img.style.display = 'none';
    spinner.style.display = 'none';
    noImg.style.display = 'block';
  }}

  const cmp = q.comparison || {{}};
  const overall = cmp.overall || 'unanimous';
  const resolved = isResolved(q);
  let html = '';

  // Resolved banner
  if (resolved && overall !== 'unanimous') {{
    html += `<div class="resolved-banner">RESOLVED</div>`;
  }}

  // Meta bar
  html += `<div class="meta">
    <span><strong>Ex:</strong> ${{q.exercise}}</span>
    <span><strong>Q:</strong> ${{q.question}}</span>
    <span><strong>Type:</strong> ${{q.type}}</span>
    <span class="status-badge status-${{resolved && overall !== 'unanimous' ? 'resolved' : overall}}">${{
      resolved && overall !== 'unanimous' ? 'resolved' : overall.replace('_',' ')}}</span>
  </div>`;

  // Accept All / Mark Correct buttons
  const unresolvedMajFields = FIELDS.filter(f => {{
    const fc = (cmp.fields || {{}})[f];
    return fc && fc.status === 'majority' && am[f] === undefined;
  }});
  const unresolvedFields = FIELDS.filter(f => {{
    const fc = (cmp.fields || {{}})[f];
    return fc && fc.status !== 'unanimous' && am[f] === undefined;
  }});

  if (unresolvedMajFields.length > 0) {{
    html += `<div style="padding:8px 12px 0">
      <button class="btn-accept-all" onclick="acceptAllMajorities()">
        Accept All Majorities (${{unresolvedMajFields.length}} field${{unresolvedMajFields.length>1?'s':''}})
      </button></div>`;
  }}
  if (overall !== 'unanimous' && unresolvedFields.length === 0 && !resolved) {{
    html += `<div style="padding:8px 12px 0">
      <button class="btn-mark-correct" onclick="markCorrect()">
        Mark as Correct
      </button></div>`;
  }}

  // Tabs
  html += `<div class="tabs">`;
  for (const field of FIELDS) {{
    const fcmp = (cmp.fields || {{}})[field] || {{ status: 'unanimous' }};
    const isActive = field === activeTab ? ' active' : '';
    const fieldAmended = am[field] !== undefined;
    let tabClass = '';
    let dotHtml = '';
    if (fcmp.status !== 'unanimous' && !fieldAmended) {{
      tabClass = ' has-issue';
      dotHtml = '<span class="tab-dot dot-red"></span>';
    }} else if (fieldAmended) {{
      tabClass = ' is-resolved';
      dotHtml = '<span class="tab-dot dot-green"></span>';
    }}
    html += `<div class="tab${{isActive}}${{tabClass}}" onclick="switchTab('${{field}}')">`
          + `${{FIELD_LABELS[field]}}${{dotHtml}}</div>`;
  }}
  html += `</div>`;

  // Tab content
  for (const field of FIELDS) {{
    const fcmp = (cmp.fields || {{}})[field] || {{ status: 'unanimous' }};
    const origVal = q.json[field];
    const isAmended = am[field] !== undefined;
    const isActive = field === activeTab ? ' active' : '';

    html += `<div class="tab-content${{isActive}}" id="tab_${{field}}">`;

    const origStr = typeof origVal === 'string' ? origVal : JSON.stringify(origVal, null, 2);

    // Store values for "Select This"
    if (!window._selectValues) window._selectValues = {{}};

    // Manual edit — collapsible, at the top
    if (fcmp.status !== 'unanimous') {{
      const editDefault = isAmended
        ? (typeof am[field] === 'string' ? am[field] : JSON.stringify(am[field], null, 2))
        : origStr;
      html += `<div class="edit-section" style="margin-bottom:10px">
        <details id="editDetails_${{field}}" ontoggle="autoSizeTextarea('edit_${{field}}')">
          <summary style="cursor:pointer;font-size:12px;font-weight:600;color:#007bff">
            Manual Edit</summary>
          <textarea class="edit-area" id="edit_${{field}}" style="margin-top:6px">${{esc(editDefault || '')}}</textarea>
          <div class="btn-row">
            <button class="btn-sm btn-save" onclick="saveField('${{field}}')">Save Edit</button>
            ${{isAmended ? '<button class="btn-sm btn-revert" onclick="revertField(\\'' + field + '\\')">Revert</button>' : ''}}
          </div>
        </details>
      </div>`;
    }}

    if (fcmp.status === 'unanimous') {{
      // Just show the value
      html += `<div class="source-card">
        <div class="source-card-header"><span>Value (all agree)</span></div>
        <div class="source-card-body">${{esc(origStr || '(empty)')}}</div>
      </div>`;
    }} else if (fcmp.status === 'majority') {{
      // Original
      const isOrigDissenter = fcmp.dissenter === 'original';
      const origClass = isOrigDissenter ? 'dissenter' : 'majority-winner';
      const origLabel = isOrigDissenter ? 'Original (dissenter)' : 'Original (majority)';
      window._selectValues[q.key + '_' + field + '_orig'] = origVal;
      html += `<div class="source-card ${{origClass}}${{isAmended && JSON.stringify(am[field])===JSON.stringify(origVal) ? ' selected' : ''}}">
        <div class="source-card-header">
          <span>${{origLabel}}</span>
          <button class="btn-select" onclick="selectValue('${{field}}','orig')">Select This</button>
          <button class="btn-copy-edit" onclick="copyToEdit('${{field}}','orig')">Copy to Edit</button>
        </div>
        <div class="source-card-body">${{esc(origStr || '(empty)')}}</div>
      </div>`;

      // Majority value
      const majStr = typeof fcmp.majority_value === 'string' ? fcmp.majority_value : JSON.stringify(fcmp.majority_value, null, 2);
      const majClass = isOrigDissenter ? 'majority-winner' : '';
      window._selectValues[q.key + '_' + field + '_majority'] = fcmp.majority_value;
      html += `<div class="source-card ${{majClass}}${{isAmended && JSON.stringify(am[field])===JSON.stringify(fcmp.majority_value) ? ' selected' : ''}}">
        <div class="source-card-header">
          <span>Majority Value</span>
          <button class="btn-select" onclick="selectValue('${{field}}','majority')">Select This</button>
          <button class="btn-copy-edit" onclick="copyToEdit('${{field}}','majority')">Copy to Edit</button>
        </div>
        <div class="source-card-body">${{diffHighlight(origVal, fcmp.majority_value)}}</div>
      </div>`;

      // Dissenter
      const disStr = typeof fcmp.dissenter_value === 'string' ? fcmp.dissenter_value : JSON.stringify(fcmp.dissenter_value, null, 2);
      window._selectValues[q.key + '_' + field + '_dissenter'] = fcmp.dissenter_value;
      html += `<div class="source-card dissenter${{isAmended && JSON.stringify(am[field])===JSON.stringify(fcmp.dissenter_value) ? ' selected' : ''}}">
        <div class="source-card-header">
          <span>Dissenter (${{fcmp.dissenter}})</span>
          <button class="btn-select" onclick="selectValue('${{field}}','dissenter')">Select This</button>
          <button class="btn-copy-edit" onclick="copyToEdit('${{field}}','dissenter')">Copy to Edit</button>
        </div>
        <div class="source-card-body">${{diffHighlight(origVal, fcmp.dissenter_value)}}</div>
      </div>`;

    }} else if (fcmp.status === 'no_majority') {{
      // Two models disagree — show both side by side
      const modelLabels = q.model_labels || [];
      const modelKeys = modelLabels.length > 0
        ? modelLabels
        : Object.keys(fcmp).filter(k => k !== 'status');

      modelKeys.forEach((mk, idx) => {{
        const val = fcmp[mk] !== undefined ? fcmp[mk]
                  : (q.model_data && q.model_data[mk] ? q.model_data[mk][field] : null);
        const valStr = typeof val === 'string' ? val : JSON.stringify(val, null, 2);
        const selKey = 'model_' + idx;
        window._selectValues[q.key + '_' + field + '_' + selKey] = val;
        const shortLabel = mk.length > 40 ? mk.substring(mk.lastIndexOf('.') + 1 || 0) : mk;
        const refVal = idx === 0 ? val : fcmp[modelKeys[0]] || null;
        html += `<div class="source-card${{isAmended && JSON.stringify(am[field])===JSON.stringify(val) ? ' selected' : ''}}">
          <div class="source-card-header">
            <span>Model ${{idx + 1}}: ${{shortLabel}}</span>
            <button class="btn-select" onclick="selectValue('${{field}}','${{selKey}}')">Select This</button>
            <button class="btn-copy-edit" onclick="copyToEdit('${{field}}','${{selKey}}')">Copy to Edit</button>
          </div>
          <div class="source-card-body">${{idx > 0 ? diffHighlight(refVal, val) : esc(valStr || '(empty)')}}</div>
        </div>`;
      }});
    }} else if (fcmp.status === 'single_model') {{
      // Only one model extraction available
      const val = fcmp.value;
      const valStr = typeof val === 'string' ? val : JSON.stringify(val, null, 2);
      window._selectValues[q.key + '_' + field + '_single'] = val;
      html += `<div class="source-card">
        <div class="source-card-header">
          <span>Single extraction (needs verification)</span>
          <button class="btn-select" onclick="selectValue('${{field}}','single')">Accept</button>
          <button class="btn-copy-edit" onclick="copyToEdit('${{field}}','single')">Copy to Edit</button>
        </div>
        <div class="source-card-body">${{esc(valStr || '(empty)')}}</div>
      </div>`;
    }}


    html += `</div>`;  // tab-content
  }}

  document.getElementById('detailPanel').innerHTML = html;
  renderSidebar();
}}

function esc(s) {{
  const d = document.createElement('div');
  d.textContent = String(s);
  return d.innerHTML;
}}

function autoSizeTextarea(id) {{
  // Runs when <details> toggles open — resize textarea to fit content
  setTimeout(() => {{
    const el = document.getElementById(id);
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.max(80, el.scrollHeight + 4) + 'px';
  }}, 10);
}}

function copyToEdit(field, sourceKey) {{
  const q = filtered[current];
  const val = window._selectValues[q.key + '_' + field + '_' + sourceKey];
  if (val === undefined) return;
  const valStr = typeof val === 'string' ? val : JSON.stringify(val, null, 2);

  // Open the details if closed
  const details = document.getElementById('editDetails_' + field);
  if (details && !details.open) details.open = true;

  // Set textarea value and auto-size
  setTimeout(() => {{
    const ta = document.getElementById('edit_' + field);
    if (!ta) return;
    ta.value = valStr;
    ta.style.height = 'auto';
    ta.style.height = Math.max(80, ta.scrollHeight + 4) + 'px';
    ta.focus();
    showToast('Copied to editor');
  }}, 50);
}}

function selectValue(field, sourceKey) {{
  const q = filtered[current];
  const val = window._selectValues[q.key + '_' + field + '_' + sourceKey];
  if (val === undefined) return;

  if (!amendments[q.key]) amendments[q.key] = {{}};
  amendments[q.key][field] = val;

  fetch('/save_amendment', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{
      key: q.key, exercise: q.exercise, question: q.question,
      field: field, value: val, amendments: amendments
    }})
  }}).then(r => r.json()).then(d => {{
    if (d.ok) {{
      q.json[field] = val;
      showToast('Selected: ' + field);
      // If question just became resolved, refresh the filter list
      if (isResolved(q)) {{
        refreshAfterResolve();
      }} else {{
        render();
        autoAdvanceTab();
      }}
    }}
  }});
}}

function firstUnresolvedTab(q) {{
  // Returns the first field tab that still needs correction, or null if all done
  const cmp = q.comparison || {{}};
  const am = amendments[q.key] || {{}};
  for (const f of FIELDS) {{
    const fc = (cmp.fields || {{}})[f];
    if (fc && fc.status !== 'unanimous' && am[f] === undefined) return f;
  }}
  return null;
}}

function autoAdvanceTab() {{
  const q = filtered[current];
  const nextTab = firstUnresolvedTab(q);
  if (nextTab) {{
    activeTab = nextTab;
    render();
  }} else {{
    // All fields resolved — move to next unresolved question
    refreshAfterResolve();
  }}
}}

function refreshAfterResolve() {{
  // Re-apply current filter so resolved questions move out of "To Check"
  const savedKey = filtered[current] ? filtered[current].key : null;
  applyFilter(currentFilter);
  // Try to stay on the same position or move to next
  if (savedKey) {{
    const idx = filtered.findIndex(q => q.key === savedKey);
    if (idx >= 0) {{
      current = idx;
    }} else {{
      current = Math.min(current, Math.max(0, filtered.length - 1));
    }}
  }}
  if (filtered.length > 0) {{
    activeTab = firstUnresolvedTab(filtered[current]) || FIELDS[0];
  }}
  renderSidebar();
  render();
}}

function markCorrect() {{
  // Mark question as resolved by flagging all remaining fields as "confirmed original"
  const q = filtered[current];
  const cmp = q.comparison || {{}};
  for (const f of FIELDS) {{
    const fc = (cmp.fields || {{}})[f];
    if (fc && fc.status !== 'unanimous' && !(amendments[q.key] || {{}})[f]) {{
      if (!amendments[q.key]) amendments[q.key] = {{}};
      amendments[q.key][f] = q.json[f];
    }}
  }}
  fetch('/save_amendment', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{
      key: q.key, exercise: q.exercise, question: q.question,
      field: '_mark_correct', value: true, amendments: amendments
    }})
  }}).then(r => r.json()).then(d => {{
    showToast('Marked correct');
    refreshAfterResolve();
  }});
}}

// Word-level diff
function diffHighlight(original, other) {{
  if (!original && !other) return '<em>(empty)</em>';
  if (!original) original = '';
  if (!other) other = '';
  const origStr = typeof original === 'string' ? original : JSON.stringify(original, null, 2);
  const otherStr = typeof other === 'string' ? other : JSON.stringify(other, null, 2);
  if (origStr === otherStr) return esc(otherStr);
  const tokenize = s => s.match(/\\S+|\\s+/g) || [];
  const origToks = tokenize(origStr);
  const otherToks = tokenize(otherStr);
  const lcs = _lcs(origToks, otherToks);
  let html = '';
  let oi = 0, ni = 0, li = 0;
  while (oi < origToks.length || ni < otherToks.length) {{
    if (li < lcs.length && oi < origToks.length && ni < otherToks.length
        && origToks[oi] === lcs[li] && otherToks[ni] === lcs[li]) {{
      html += esc(otherToks[ni]); oi++; ni++; li++;
    }} else if (li < lcs.length && ni < otherToks.length && otherToks[ni] === lcs[li]) {{
      html += `<del>${{esc(origToks[oi])}}</del>`; oi++;
    }} else if (li < lcs.length && oi < origToks.length && origToks[oi] === lcs[li]) {{
      html += `<ins>${{esc(otherToks[ni])}}</ins>`; ni++;
    }} else {{
      if (oi < origToks.length && (li >= lcs.length || origToks[oi] !== lcs[li])) {{
        html += `<del>${{esc(origToks[oi])}}</del>`; oi++;
      }}
      if (ni < otherToks.length && (li >= lcs.length || otherToks[ni] !== lcs[li])) {{
        html += `<ins>${{esc(otherToks[ni])}}</ins>`; ni++;
      }}
    }}
  }}
  return html;
}}

function _lcs(a, b) {{
  const m = a.length, n = b.length;
  if (m === 0 || n === 0) return [];
  if (m * n > 500000) return [];
  const dp = Array.from({{length: m+1}}, () => new Uint16Array(n+1));
  for (let i = 1; i <= m; i++)
    for (let j = 1; j <= n; j++)
      dp[i][j] = a[i-1] === b[j-1] ? dp[i-1][j-1]+1 : Math.max(dp[i-1][j], dp[i][j-1]);
  const result = [];
  let i = m, j = n;
  while (i > 0 && j > 0) {{
    if (a[i-1] === b[j-1]) {{ result.unshift(a[i-1]); i--; j--; }}
    else if (dp[i-1][j] >= dp[i][j-1]) i--;
    else j--;
  }}
  return result;
}}

function saveField(field) {{
  const q = filtered[current];
  const el = document.getElementById('edit_' + field);
  let val = el.value;
  if (field !== 'question_text' && field !== 'type') {{
    try {{ val = JSON.parse(val); }} catch(e) {{}}
  }}
  if (!amendments[q.key]) amendments[q.key] = {{}};
  amendments[q.key][field] = val;
  fetch('/save_amendment', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{
      key: q.key, exercise: q.exercise, question: q.question,
      field: field, value: val, amendments: amendments
    }})
  }}).then(r => r.json()).then(d => {{
    if (d.ok) {{ q.json[field] = val; showToast('Saved: ' + field);
      if (isResolved(q)) {{ refreshAfterResolve(); }} else {{ render(); autoAdvanceTab(); }} }}
    else {{ showToast('Error: ' + (d.error || 'unknown')); }}
  }});
}}

function acceptAllMajorities() {{
  const q = filtered[current];
  const cmp = q.comparison || {{}};
  const am = amendments[q.key] || {{}};
  const fields = FIELDS.filter(f => {{
    const fc = (cmp.fields || {{}})[f];
    return fc && fc.status === 'majority' && am[f] === undefined;
  }});
  let i = 0;
  function next() {{
    if (i >= fields.length) {{
      showToast(`Accepted ${{fields.length}} majority value(s)`);
      refreshAfterResolve();
      return;
    }}
    const field = fields[i++];
    const fc = cmp.fields[field];
    const val = fc.majority_value;
    if (!amendments[q.key]) amendments[q.key] = {{}};
    amendments[q.key][field] = val;
    q.json[field] = val;
    fetch('/save_amendment', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{
        key: q.key, exercise: q.exercise, question: q.question,
        field: field, value: val, amendments: amendments
      }})
    }}).then(r => r.json()).then(() => next());
  }}
  next();
}}

function revertField(field) {{
  const q = filtered[current];
  if (amendments[q.key]) {{
    delete amendments[q.key][field];
    if (Object.keys(amendments[q.key]).length === 0) delete amendments[q.key];
  }}
  fetch('/revert_amendment', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{
      key: q.key, exercise: q.exercise, question: q.question,
      field: field, amendments: amendments
    }})
  }}).then(r => r.json()).then(d => {{
    if (d.ok) {{ q.json[field] = d.original_value; showToast('Reverted'); render(); }}
  }});
}}

function showToast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 1500);
}}

function go(delta) {{
  current = Math.max(0, Math.min(filtered.length - 1, current + delta));
  activeTab = firstUnresolvedTab(filtered[current]) || FIELDS[0];
  render();
}}
function goTo(i) {{ current = i; activeTab = firstUnresolvedTab(filtered[current]) || FIELDS[0]; render(); }}

function jumpToNextIssue() {{
  for (let i = current + 1; i < filtered.length; i++) {{
    if (needsReview(filtered[i])) {{ current = i; activeTab = firstUnresolvedTab(filtered[i]) || FIELDS[0]; render(); return; }}
  }}
  // Wrap around
  for (let i = 0; i < current; i++) {{
    if (needsReview(filtered[i])) {{ current = i; activeTab = firstUnresolvedTab(filtered[i]) || FIELDS[0]; render(); return; }}
  }}
  showToast('No more unresolved issues');
}}

function needsReview(q) {{
  const cmp = q.comparison || {{}};
  if (cmp.overall === 'unanimous') return false;
  const am = amendments[q.key] || {{}};
  const fields = cmp.fields || {{}};
  for (const f of FIELDS) {{
    if (fields[f] && fields[f].status !== 'unanimous' && am[f] === undefined) return true;
  }}
  return false;
}}

// Keyboard
document.addEventListener('keydown', e => {{
  if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;
  if (e.key === 'ArrowLeft' || e.key === 'a') go(-1);
  if (e.key === 'ArrowRight' || e.key === 'd') go(1);
  if (e.key === 'n') jumpToNextIssue();
  // Tab switching with 1-4
  if (e.key >= '1' && e.key <= '4') {{ activeTab = FIELDS[parseInt(e.key)-1]; render(); }}
}});
</script>
</body>
</html>"""


class ViewerHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler for the viewer UI."""

    html_content = ""
    original_backups = {}  # key -> {field: original_value}

    def do_GET(self):
        if self.path == "/amendments":
            # Always serve fresh amendments from disk
            data = _load_amendments()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
        elif self.path.startswith("/screenshot/"):
            # Lazy-load screenshots: /screenshot/{exercise}/{question}
            parts = self.path.split("/")
            if len(parts) == 4:
                try:
                    ex, qn = int(parts[2]), int(parts[3])
                    scrn = screenshot_path(ex, qn)
                    if scrn and scrn.exists():
                        data = scrn.read_bytes()
                        self.send_response(200)
                        self.send_header("Content-Type", "image/png")
                        self.send_header("Cache-Control", "max-age=3600")
                        self.end_headers()
                        self.wfile.write(data)
                        return
                except (ValueError, IndexError):
                    pass
            self.send_response(404)
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self.html_content.encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        if self.path == "/save_amendment":
            try:
                ex, qn = body["exercise"], body["question"]
                field, value = body["field"], body["value"]
                key = body["key"]

                # Load merged json, or bootstrap from a model file
                orig_json = load_structured_json(ex, qn)
                if orig_json is None:
                    # No merged file yet — bootstrap from first model file
                    orig_json = _load_any_model_json(ex, qn) or {}

                # Backup original value before first amendment
                if key not in ViewerHandler.original_backups:
                    ViewerHandler.original_backups[key] = {}
                if field not in ViewerHandler.original_backups[key]:
                    ViewerHandler.original_backups[key][field] = orig_json.get(field)

                # Update the merged JSON file directly
                # Skip meta-fields like _mark_correct
                if not field.startswith("_"):
                    orig_json[field] = value
                    json_dir = STRUCTURED_DIR / str(ex) / "json"
                    json_dir.mkdir(parents=True, exist_ok=True)
                    json_path = json_dir / f"{qn}.json"
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(orig_json, f, indent=2, ensure_ascii=False)

                # Save amendments log
                _save_amendments(body.get("amendments", {}))

                self._json_response({"ok": True})
            except Exception as e:
                self._json_response({"ok": False, "error": str(e)}, 500)

        elif self.path == "/revert_amendment":
            try:
                ex, qn = body["exercise"], body["question"]
                field = body["field"]
                key = body["key"]

                # Restore from backup
                backup_val = None
                if key in ViewerHandler.original_backups and field in ViewerHandler.original_backups[key]:
                    backup_val = ViewerHandler.original_backups[key][field]
                    del ViewerHandler.original_backups[key][field]

                    orig_json = load_structured_json(ex, qn)
                    if orig_json:
                        orig_json[field] = backup_val
                        json_path = STRUCTURED_DIR / str(ex) / "json" / f"{qn}.json"
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump(orig_json, f, indent=2, ensure_ascii=False)

                _save_amendments(body.get("amendments", {}))
                self._json_response({"ok": True, "original_value": backup_val})
            except Exception as e:
                self._json_response({"ok": False, "error": str(e)}, 500)
        else:
            self.send_response(404)
            self.end_headers()

    def _json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def log_message(self, format, *args):
        pass


def run_viewer_server(port: int = 8900, filter_status: str = "all"):
    """Launch the comparison viewer."""
    print("Loading questions...")
    all_items = enumerate_zanichelli_questions()
    n_merged = sum(1 for i in all_items if i["merged"])
    n_unmerged = sum(1 for i in all_items if not i["merged"])
    print(f"  {len(all_items)} questions found ({n_merged} merged, {n_unmerged} need review)")

    # Build question data for the UI (screenshots loaded lazily via /screenshot/ endpoint)
    print("Building viewer data...")
    questions_data = []
    for item in sorted(all_items, key=lambda x: (x["exercise"], x["question"])):
        ex, qn = item["exercise"], item["question"]
        key = f"{ex}_{qn}"

        if item["merged"]:
            # Merged (agreed or manually resolved) — show as unanimous
            structured = load_structured_json(ex, qn) or {}
            cmp_data = {"overall": "unanimous", "fields": {
                f: {"status": "unanimous"} for f in COMPARED_FIELDS
            }}
            model_labels = list(item["model_files"].keys())
            questions_data.append({
                "exercise": ex, "question": qn, "key": key,
                "type": item["type"], "has_image": item["has_image"],
                "screenshot": f"/screenshot/{ex}/{qn}",
                "json": structured,
                "comparison": cmp_data,
                "model_labels": model_labels,
            })
        else:
            # Unmerged — live comparison from the two model files
            model_labels = sorted(item["model_files"].keys())
            model_data = {}
            for label in model_labels:
                p = Path(item["model_files"][label])
                model_data[label] = json.loads(p.read_text(encoding="utf-8"))

            # Use first model's data as display json
            first_data = model_data[model_labels[0]] if model_labels else {}

            if len(model_labels) == 2:
                data_a = model_data[model_labels[0]]
                data_b = model_data[model_labels[1]]
                cmp_fields = {}
                has_disagreement = False
                for field in COMPARED_FIELDS:
                    result = compare_two_models(field, data_a, data_b)
                    if result["status"] == "agreed":
                        cmp_fields[field] = {"status": "unanimous"}
                    else:
                        has_disagreement = True
                        cmp_fields[field] = {
                            "status": "no_majority",
                            model_labels[0]: result["value_a"],
                            model_labels[1]: result["value_b"],
                        }
                overall = "no_majority" if has_disagreement else "unanimous"
                cmp_data = {"overall": overall, "fields": cmp_fields}
            elif len(model_labels) == 1:
                # Only one model — nothing to compare, treat as needing review
                cmp_data = {"overall": "single_model", "fields": {
                    f: {"status": "single_model", "value": first_data.get(f)}
                    for f in COMPARED_FIELDS
                }}
            else:
                cmp_data = {"overall": "no_data", "fields": {}}

            questions_data.append({
                "exercise": ex, "question": qn, "key": key,
                "type": item["type"], "has_image": item["has_image"],
                "screenshot": f"/screenshot/{ex}/{qn}",
                "json": first_data,
                "comparison": cmp_data,
                "model_labels": model_labels,
                "model_data": model_data,
            })

    # Show counts per filter
    amendments = _load_amendments()
    counts = defaultdict(int)
    to_check = 0
    for q in questions_data:
        overall = q["comparison"]["overall"]
        counts[overall] += 1
        # "To Check" = has disagreements and not all fields amended
        if overall not in ("unanimous",):
            key = q["key"]
            am = amendments.get(key, {})
            dis_fields = [f for f, fc in q["comparison"].get("fields", {}).items()
                          if fc.get("status") not in ("unanimous",)]
            if not all(f in am for f in dis_fields):
                to_check += 1
    resolved = len(amendments)
    print(f"\n  Filter counts:")
    print(f"    All:          {len(questions_data)}")
    print(f"    To Check:     {to_check}")
    print(f"    Resolved:     {resolved}")
    print(f"    Unanimous:    {counts.get('unanimous', 0)}")
    print(f"    Disagreement: {counts.get('no_majority', 0)}")
    if counts.get('single_model', 0):
        print(f"    Single model: {counts.get('single_model', 0)}")

    # Apply initial filter
    if filter_status != "all":
        questions_data = [q for q in questions_data if q["comparison"]["overall"] == filter_status]

    ViewerHandler.html_content = _build_viewer_html(questions_data)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), ViewerHandler) as httpd:
        url = f"http://localhost:{port}"
        print(f"\nViewer running at {url}")
        print("Keyboard: Arrow keys / a,d = navigate   n = next issue")
        print("Press Ctrl+C to stop.\n")
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nViewer stopped.")
            am = _load_amendments()
            if am:
                print(f"  {len(am)} questions have amendments")


if __name__ == "__main__":
    cli()
