#!/usr/bin/env python3
"""
Question preprocessor — dual-model extraction with automatic agreement merge.

Runs TWO models as equal peers:
  Model A  → {q}.{label_a}.json
  Model B  → {q}.{label_b}.json

Then compares them field-by-field:
  - If they agree on all fields → auto-create {q}.json  (ground truth)
  - If they disagree           → no {q}.json; must be resolved in the viewer

USAGE:
    python 2_question_preprocessor.py -a                        # all exercises
    python 2_question_preprocessor.py -a --workers 4            # 4 parallel questions
    python 2_question_preprocessor.py -a --force --keep-amend   # re-run non-amended only
"""

# Suppress gRPC/ALTS warnings before any imports
import os
os.environ.setdefault("GRPC_VERBOSITY", "NONE")
os.environ.setdefault("GLOG_minloglevel", "2")

import click
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.core.exceptions import ProcessingError, ConfigurationError

# ---------------------------------------------------------------------------
# Model configuration — both are peers
# ---------------------------------------------------------------------------

MODEL_SPECS = [
    ("google", "gemini-3-flash-preview"),
    ("harvard", "us.anthropic.claude-sonnet-4-6"),
]

COMPARE_FIELDS = ("type", "question_text", "choices", "answers")

BASE_DIR = Path(__file__).parent                      # myzanichelli/
RAW_DIR = BASE_DIR / "raw"
STRUCTURED_DIR = BASE_DIR / "structured"
PROMPTS_DIR = BASE_DIR.parent.parent / "prompts"      # datasets/prompts
VALIDATION_DIR = BASE_DIR.parent.parent / "validation"
AMENDMENTS_FILE = VALIDATION_DIR / "viewer_amendments.json"
LOG_DIR = BASE_DIR.parent.parent / "logs"

# ---------------------------------------------------------------------------
# Logging — thread-safe, single file handle
# ---------------------------------------------------------------------------

_verbose_flag = False
_log_file = None
_log_lock = threading.Lock()


def _open_log():
    global _log_file
    if _log_file is None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        _log_file = open(LOG_DIR / "preprocessor.log", "a", encoding="utf-8")


def _close_log():
    global _log_file
    if _log_file is not None:
        _log_file.close()
        _log_file = None


@contextmanager
def suppress_stdout():
    """Redirect stdout to log file unless verbose. Thread-safe."""
    if _verbose_flag:
        yield
        return
    _open_log()
    old_stdout = sys.stdout
    with _log_lock:
        sys.stdout = _log_file
    try:
        yield
    finally:
        with _log_lock:
            sys.stdout = old_stdout


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def count_png_files_in_raw(exercise: int) -> int:
    raw_path = RAW_DIR / str(exercise) / "screenshot"
    if not raw_path.exists():
        return 0
    return len(list(raw_path.glob("*.png")))


def load_amendments() -> dict:
    if AMENDMENTS_FILE.exists():
        return json.loads(AMENDMENTS_FILE.read_text(encoding="utf-8"))
    return {}


def make_label(provider_type: str, model_name: str) -> str:
    return f"{provider_type}_{model_name}".replace("/", "_")


def _parse_json_response(text: str) -> dict:
    m = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return {"_raw_response": text, "error": "json_parse_failed"}


# ---------------------------------------------------------------------------
# Provider pool — one provider per (label, worker_id) for thread safety
# ---------------------------------------------------------------------------

_providers = {}         # (label, worker_id) -> provider
_providers_lock = threading.Lock()
_prompt_manager = None
_prompt_lock = threading.Lock()

# Thread-local storage for worker IDs
_thread_local = threading.local()


def _get_prompt_manager():
    global _prompt_manager
    if _prompt_manager is None:
        with _prompt_lock:
            if _prompt_manager is None:
                from modules.managers.prompt_manager import PromptManager
                with suppress_stdout():
                    _prompt_manager = PromptManager(prompts_dir=PROMPTS_DIR)
    return _prompt_manager


def _get_provider(provider_type: str, model_name: str, worker_id: int = 0):
    """Get or create a provider instance. Each worker gets its own instance."""
    label = make_label(provider_type, model_name)
    key = (label, worker_id)
    if key not in _providers:
        with _providers_lock:
            if key not in _providers:
                from modules.llm.factory import create_llm_provider
                with suppress_stdout():
                    _providers[key] = create_llm_provider(
                        provider_type, model_name, max_tokens=16384)
    return _providers[key]


def init_providers(n_workers: int):
    """Pre-initialize all provider instances for all workers."""
    _get_prompt_manager()
    for w in range(n_workers):
        for p, m in MODEL_SPECS:
            _get_provider(p, m, worker_id=w)


# ---------------------------------------------------------------------------
# Single-model extraction
# ---------------------------------------------------------------------------

def extract_question(
    provider_type: str,
    model_name: str,
    exercise: int,
    question: int,
    force: bool = False,
    worker_id: int = 0,
    html_text: str = None,
) -> tuple:
    """
    Extract a single question with a given model.
    Returns (label, data_dict, elapsed_seconds) or (label, None, elapsed).
    """
    label = make_label(provider_type, model_name)
    out_file = STRUCTURED_DIR / str(exercise) / "json" / f"{question}.{label}.json"

    if out_file.exists() and not force:
        data = json.loads(out_file.read_text(encoding="utf-8"))
        return label, data, 0.0
    if out_file.exists() and force:
        out_file.unlink()

    img_path = RAW_DIR / str(exercise) / "screenshot" / f"{question}.png"
    if not img_path.exists():
        return label, None, 0.0

    # Read HTML text if not pre-loaded
    if html_text is None:
        html_path = RAW_DIR / str(exercise) / "html" / f"{question}.html"
        html_text = html_path.read_text(encoding="utf-8") if html_path.exists() else ""

    pm = _get_prompt_manager()
    system_prompt = pm.get_system_prompt()

    # Use unified prompt — model determines type from the screenshot
    unified_template = pm.prompts.get("extract_text", "")
    if not unified_template:
        raise RuntimeError("Missing prompts/extract_text.txt")
    user_prompt = unified_template.replace("{html_text}", html_text or "")

    provider = _get_provider(provider_type, model_name, worker_id=worker_id)

    # Per-question log in structured/{ex}/log/{q}.log
    log_dir = STRUCTURED_DIR / str(exercise) / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{question}.log"

    def _log(msg: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as lf:
            lf.write(f"[{ts}] [{label}] {msg}\n")

    t0 = time.time()
    try:
        _log(f"START prompt=unified image={img_path.name}")
        with suppress_stdout():
            response_text, token_meta = provider.query(
                prompt=user_prompt,
                system_prompt=system_prompt,
                image_path=str(img_path),
            )
        elapsed = time.time() - t0
        _log(f"RESPONSE elapsed={elapsed:.1f}s tokens={token_meta}")

        # Save raw response for every request
        raw_file = log_dir / f"{question}.{label}.response.txt"
        raw_file.write_text(response_text, encoding="utf-8")

        parsed = _parse_json_response(response_text)
        if "error" in parsed and parsed.get("error") == "json_parse_failed":
            _log(f"PARSE_FAILED raw_length={len(response_text)}")
            # Save raw response for debugging
            raw_file = log_dir / f"{question}.{label}.raw.txt"
            raw_file.write_text(response_text, encoding="utf-8")
            return label, None, elapsed

        parsed["exercise"] = exercise
        parsed["question"] = question
        parsed["_extraction"] = {
            "model": label,
            "token_metadata": token_meta,
            "timestamp": datetime.now().isoformat(),
        }

        img_jpg = RAW_DIR / str(exercise) / "imgs" / f"{question}.jpg"
        if img_jpg.exists():
            parsed.setdefault("has_image", True)
            parsed.setdefault("image", str(img_jpg))

        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2, ensure_ascii=False)

        _log(f"OK saved={out_file.name}")
        return label, parsed, elapsed

    except Exception as e:
        elapsed = time.time() - t0
        _log(f"FAILED elapsed={elapsed:.1f}s error={e}")
        with suppress_stdout():
            print(f"FAILED {label} ex={exercise} q={question}: {e}")
        return label, None, elapsed


# ---------------------------------------------------------------------------
# Process a single question (both models in parallel)
# ---------------------------------------------------------------------------

def process_one_question(ex: int, q: int, force: bool, worker_id: int) -> dict:
    """
    Run both models on a single question in parallel, then auto-merge.
    Returns a dict with status info.
    """
    gt_file = STRUCTURED_DIR / str(ex) / "json" / f"{q}.json"
    if gt_file.exists() and force:
        gt_file.unlink()

    # Pre-read HTML text once for both models
    html_path = RAW_DIR / str(ex) / "html" / f"{q}.html"
    html_text = html_path.read_text(encoding="utf-8") if html_path.exists() else ""

    # Run both models in parallel
    results = {}
    status_parts = []

    with ThreadPoolExecutor(max_workers=len(MODEL_SPECS)) as model_executor:
        futures = {}
        for i, (provider_type, model_name) in enumerate(MODEL_SPECS):
            fut = model_executor.submit(
                extract_question,
                provider_type, model_name, ex, q,
                force=force,
                worker_id=worker_id,
                html_text=html_text,
            )
            futures[fut] = (provider_type, model_name)

        for fut in as_completed(futures):
            label, data, elapsed = fut.result()
            if data is not None:
                results[label] = data
                t_str = f"{elapsed:.1f}s" if elapsed > 0 else "cached"
                status_parts.append(f"{label.split('_')[0]}:{t_str}")
            else:
                status_parts.append(f"{label.split('_')[0]}:FAIL")

    # Auto-merge + log result
    log_dir = STRUCTURED_DIR / str(ex) / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{q}.log"

    def _log_merge(msg: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as lf:
            lf.write(f"[{ts}] [merge] {msg}\n")

    info = {"ex": ex, "q": q, "status_parts": status_parts}

    if len(results) < 2:
        info["merge"] = "incomplete"
        info["stat"] = "failed"
        _log_merge(f"INCOMPLETE models_ok={len(results)}/{len(MODEL_SPECS)}")
    else:
        data_list = list(results.values())
        merged = auto_merge(data_list[0], data_list[1], ex, q)
        if merged:
            info["merge"] = "OK"
            info["stat"] = "agreed"
            _log_merge("AGREED → merged to {q}.json")
        else:
            _, diffs = check_agreement(data_list[0], data_list[1])
            info["merge"] = f"DIFF[{','.join(diffs)}]"
            info["stat"] = "disagreed"
            _log_merge(f"DISAGREED fields={','.join(diffs)}")

    return info


# ---------------------------------------------------------------------------
# Agreement check & auto-merge
# ---------------------------------------------------------------------------

def _normalize(val):
    if val is None:
        return None
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, (list, dict)):
        return json.dumps(val, sort_keys=True, ensure_ascii=False)
    return val


def check_agreement(data_a: dict, data_b: dict) -> tuple:
    disagreements = []
    for field in COMPARE_FIELDS:
        va = _normalize(data_a.get(field))
        vb = _normalize(data_b.get(field))
        if va != vb:
            disagreements.append(field)
    return len(disagreements) == 0, disagreements


def auto_merge(data_a: dict, data_b: dict, exercise: int, question: int) -> bool:
    agree, _ = check_agreement(data_a, data_b)
    if not agree:
        return False

    gt = {}
    for field in COMPARE_FIELDS:
        gt[field] = data_a.get(field)

    for k in ("question_title", "image", "language", "has_image", "instructions"):
        if k in data_a:
            gt[k] = data_a[k]
        elif k in data_b:
            gt[k] = data_b[k]

    gt["exercise"] = exercise
    gt["question"] = question
    gt["_ground_truth"] = {
        "method": "auto_merge",
        "timestamp": datetime.now().isoformat(),
    }

    out_file = STRUCTURED_DIR / str(exercise) / "json" / f"{question}.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(gt, f, indent=2, ensure_ascii=False)
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Show all model output')
@click.option('--exercise', '-e', multiple=True, type=int, help='Exercise number(s)')
@click.option('--all', '-a', is_flag=True, help='Process all exercises 1-57')
@click.option('--min-question', default=1, show_default=True)
@click.option('--max-question', default=20, show_default=True)
@click.option('--force', is_flag=True, help='Re-run all extractions')
@click.option('--keep-amend', is_flag=True, help='Skip manually amended questions')
@click.option('--workers', '-w', default=2, show_default=True,
              help='Number of questions to process in parallel')
def main(verbose, exercise, all, min_question, max_question, force, keep_amend, workers):
    """Dual-model question preprocessor with parallel execution."""
    global _verbose_flag
    _verbose_flag = verbose

    try:
        from tqdm import tqdm

        if all:
            exercise = tuple(range(1, 58))
        elif not exercise:
            exercise = tuple(range(1, 58))

        amendments = load_amendments() if keep_amend else {}

        print("=== Dual-Model Question Preprocessor ===")
        for p, m in MODEL_SPECS:
            print(f"  {make_label(p, m)}")
        print(f"Workers: {workers}")
        if force:
            print(f"Force: yes  Keep-amend: {keep_amend}")
        if not verbose:
            print(f"Logs: {LOG_DIR / 'preprocessor.log'}")

        # Pre-init all providers for all workers
        print("Initializing providers...")
        init_providers(workers)
        print()

        # Build work list
        work = []
        for ex in exercise:
            png_count = count_png_files_in_raw(ex)
            eff_max = min(max_question, png_count)
            if eff_max < min_question:
                continue
            for q in range(min_question, eff_max + 1):
                key = f"{ex}_{q}"
                gt_file = STRUCTURED_DIR / str(ex) / "json" / f"{q}.json"
                if keep_amend and key in amendments:
                    continue
                if gt_file.exists() and not force:
                    continue
                work.append((ex, q))

        if not work:
            print("Nothing to process.")
            return

        stats = {"total": 0, "agreed": 0, "disagreed": 0, "failed": 0}

        if workers <= 1:
            # Sequential mode — simple tqdm loop
            pbar = tqdm(work, desc="Processing", unit="q",
                        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]")
            for ex, q in pbar:
                pbar.set_description(f"Ex {ex} Q{q}")
                info = process_one_question(ex, q, force, worker_id=0)
                stats["total"] += 1
                stats[info["stat"]] += 1
                pbar.set_postfix_str(
                    f"{' | '.join(info['status_parts'])} → {info['merge']}")
            pbar.close()
        else:
            # Parallel mode — thread pool of workers
            pbar = tqdm(total=len(work), desc="Processing", unit="q",
                        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]")

            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_item = {}
                for idx, (ex, q) in enumerate(work):
                    wid = idx % workers
                    fut = executor.submit(process_one_question, ex, q, force, wid)
                    future_to_item[fut] = (ex, q)

                for fut in as_completed(future_to_item):
                    ex, q = future_to_item[fut]
                    try:
                        info = fut.result()
                        stats["total"] += 1
                        stats[info["stat"]] += 1
                        pbar.set_postfix_str(
                            f"{ex}/{q} {' | '.join(info['status_parts'])} → {info['merge']}")
                    except Exception as e:
                        stats["total"] += 1
                        stats["failed"] += 1
                        pbar.set_postfix_str(f"{ex}/{q} ERROR: {e}")
                    pbar.update(1)

            pbar.close()

        # Summary
        print(f"\n{'='*50}")
        print(f"SUMMARY")
        print(f"{'='*50}")
        print(f"Total compared:  {stats['total']}")
        print(f"Auto-merged:     {stats['agreed']}")
        print(f"Need review:     {stats['disagreed']}")
        if keep_amend:
            print(f"Skipped:         {len(amendments)} (amended)")
        print(f"Failed:          {stats['failed']}")
        if stats['total'] > 0:
            pct = stats['agreed'] / stats['total'] * 100
            print(f"Agreement rate:  {pct:.1f}%")
        if stats['disagreed'] > 0:
            print(f"\nRun 'python questions/validation.py viewer' to review disagreements.")

    except (ConfigurationError, ProcessingError) as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        _close_log()


if __name__ == "__main__":
    exit(main())
