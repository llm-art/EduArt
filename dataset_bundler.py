#!/usr/bin/env python3
"""
Dataset Bundler Script

Navigates structured/ folders in questions/, extracts JSON files,
creates TXT questions, copies optimized images, and generates reports.
"""

import os
import sys
import json
import shutil
import copy
import click
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add questions directory to path for shared modules
sys.path.insert(0, str(Path(__file__).parent / "questions"))

from modules.llm.factory import create_llm_provider
from modules.services.categorization_service import categorize_question
from modules.processors.dataset_discovery import (
    find_structured_folders,
    find_json_files_in_structured,
    find_associated_image,
    extract_question_data,
    process_true_false_answers,
    create_txt_content,
)
from modules.managers.dataset_report_manager import (
    get_next_file_id,
    get_previous_version,
    collect_statistics_from_metadata,
    generate_report,
    generate_metadata,
    REPORT_CONFIG,
)


@click.command()
@click.option('--question-type',
              multiple=True,
              default=['multiple_choice_radio', 'multiple_choice_check', 'true_false',
                       'completion_open', 'completion_closed', 'positioning', 'select_errors'],
              help='Question type(s) to include (can be specified multiple times). Default: all types')
@click.option('--version', type=float, help='Specify version number for the report')
@click.option('--output-dir', default='dataset', help='Output directory for the dataset (default: dataset)')
@click.option('--categorization-model', default=None,
              help='LLM model for categorization (e.g., google/gemini-2.5-flash-lite). Omit to skip.')
@click.option('--max-questions', type=int, default=None,
              help='Maximum number of questions to process (default: all)')
def main(question_type, version, output_dir, categorization_model, max_questions):
  """Main function to process all JSON files and create dataset."""
  start_time = datetime.now()

  # Convert question_type tuple to list
  question_types = list(question_type)

  print(f"Filtering by question types: {', '.join(question_types)}")

  # Initialize categorization provider if requested
  categorization_provider = None
  if categorization_model:
    try:
      parts = categorization_model.split('/', 1)
      if len(parts) != 2:
        raise ValueError(f"Expected format 'provider/model', got '{categorization_model}'")
      cat_provider_type, cat_model_name = parts
      categorization_provider = create_llm_provider(cat_provider_type, cat_model_name)
      print(f"Categorization enabled with model: {categorization_model}")
    except Exception as e:
      print(f"Warning: Could not initialize categorization provider: {e}")
      print("Continuing without categorization.")

  # Read previous version BEFORE removing the dataset directory
  dataset_dir = output_dir
  previous_version = None
  if version is None:
    previous_version = get_previous_version(dataset_dir)

  # Remove existing dataset directory for fresh start
  if os.path.exists(dataset_dir):
    shutil.rmtree(dataset_dir)
    print(f"Removed existing dataset directory: {dataset_dir}")

  # Create dataset directory structure
  dataset_path = Path(dataset_dir)
  data_dir = dataset_path / "data"
  metadata_dir = dataset_path / "metadata"
  imgs_dir = dataset_path / "imgs"

  data_dir.mkdir(parents=True, exist_ok=True)
  metadata_dir.mkdir(parents=True, exist_ok=True)
  imgs_dir.mkdir(parents=True, exist_ok=True)

  # Create documentation directory for example screenshots
  documentation_dir = dataset_path / "documentation"
  documentation_dir.mkdir(parents=True, exist_ok=True)

  # Find all structured folders
  structured_folders = find_structured_folders()

  if not structured_folders:
    print("No structured folders found in questions/")
    return

  print(f"Found {len(structured_folders)} structured folder(s)")

  processed_files = []
  skipped_files = []
  processed_metadata_files = []

  # Track image files to avoid duplicates
  # Key: absolute path to source image, Value: (file_id, extension) of first copy
  image_mapping = {}

  # Track first question of each type from myzanichelli for documentation
  # Key: question_type, Value: dict with screenshot info
  first_question_by_type = {}


  # Track categorization statistics
  categorization_stats = {
      'attempted': 0,
      'succeeded': 0,
      'failed': 0,
      'total_input_tokens': 0,
      'total_output_tokens': 0,
      'total_processing_time': 0.0,
  }

  # Collect all JSON files from all structured folders first
  all_json_files = []
  for structured_path in structured_folders:
    json_files = find_json_files_in_structured(structured_path, question_types)
    all_json_files.extend(json_files)

  if not all_json_files:
    print("No matching JSON files found in any structured folders")
    return

  # Sort all files by: source_name, subfolder (as int), json filename (as int)
  def sort_key(item):
    json_file_path, source_name, subfolder_name = item
    try:
      subfolder_num = int(subfolder_name)
    except ValueError:
      subfolder_num = 0

    try:
      json_filename = json_file_path.stem  # filename without extension
      json_num = int(json_filename)
    except ValueError:
      json_num = 0

    return (source_name, subfolder_num, json_num)

  all_json_files.sort(key=sort_key)

  print(
    f"Found {len(all_json_files)} JSON file(s) with matching question types across all sources")
  if max_questions is not None:
    print(f"Limiting to {max_questions} question(s)")

  # Process each JSON file
  for json_file_path, source_name, subfolder_name in all_json_files:
    if max_questions is not None and len(processed_metadata_files) >= max_questions:
      print(f"\nReached maximum of {max_questions} questions, stopping.")
      break

    try:
        # Read JSON file
      with open(json_file_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

      # Handle both single question and multiple questions format
      questions_to_process = []
      parent_metadata = {}
      if "questions" in json_data and isinstance(json_data["questions"], list):
        # Multiple questions in one file - capture top-level metadata
        parent_metadata = {k: v for k, v in json_data.items() if k != "questions"}
        # Filter by type
        for question in json_data["questions"]:
          if question.get("type") in question_types:
            questions_to_process.append(question)
      elif "type" in json_data:
        # Single question format
        if json_data.get("type") in question_types:
          questions_to_process.append(json_data)

      # Process each question
      for question_data in questions_to_process:
        # Get next file identifier
        file_id = get_next_file_id(data_dir)

        # Extract question data
        question_title, question_text, choices, question_type_val = extract_question_data(
            question_data)

        # Create TXT file content
        txt_content = create_txt_content(
            question_title, question_text, choices, question_type_val)

        # Write TXT file to data/ folder
        txt_filename = f"{file_id}.txt"
        txt_path = data_dir / txt_filename
        with open(txt_path, 'w', encoding='utf-8') as f:
          f.write(txt_content)

        # Look for and copy associated image
        # Handle both "images" (array) and "image" (single) fields
        image_ref = None
        if "images" in question_data:
          images = question_data.get("images", [])
          if images and len(images) > 0:
            image_ref = images[0]
        elif "image" in question_data:
          image_ref = question_data.get("image")

        # Get exercise and question numbers for image lookup
        exercise_num = question_data.get("exercise")
        question_num = question_data.get("question")

        image_file = find_associated_image(
          json_file_path, image_ref, source_name, exercise_num, question_num)

        # Add source information to the question data
        question_data_copy = question_data.copy()
        # Merge parent-level metadata (question-level fields take precedence)
        for key, value in parent_metadata.items():
          if key not in question_data_copy:
            question_data_copy[key] = value
        question_data_copy = process_true_false_answers(question_data_copy)
        question_data_copy['source'] = f"{source_name}/{subfolder_name}"
        question_data_copy['source_file'] = str(json_file_path)

        # Always initialize the 4 category fields (null when uncategorized)
        question_data_copy['art_historical'] = None
        question_data_copy['cultural_tradition'] = None
        question_data_copy['disciplinary_domain'] = None
        question_data_copy['epistemic_level'] = None

        # Categorize question if provider is available
        if categorization_provider:
          categorization_stats['attempted'] += 1
          categories, cat_ai_call = categorize_question(
              categorization_provider, question_text, choices, question_title)
          if categories:
            question_data_copy['art_historical'] = categories['art_historical']
            question_data_copy['cultural_tradition'] = categories['cultural_tradition']
            question_data_copy['disciplinary_domain'] = categories['disciplinary_domain']
            question_data_copy['epistemic_level'] = categories['epistemic_level']
            categorization_stats['succeeded'] += 1
          else:
            categorization_stats['failed'] += 1
          if cat_ai_call:
            # Deep-copy existing ai_calls list before appending
            existing_ai_calls = copy.deepcopy(question_data_copy.get('ai_calls', []))
            existing_ai_calls.append(cat_ai_call)
            question_data_copy['ai_calls'] = existing_ai_calls
            categorization_stats['total_input_tokens'] += cat_ai_call.get('input_tokens', 0)
            categorization_stats['total_output_tokens'] += cat_ai_call.get('output_tokens', 0)
            categorization_stats['total_processing_time'] += cat_ai_call.get('processing_time', 0.0)

        # Normalize image metadata format
        # Remove old "images" array field if present
        if "images" in question_data_copy:
          del question_data_copy["images"]

        # Set standardized image fields
        if image_file:
          # Get absolute path of source image for deduplication
          image_file_abs = image_file.resolve()

          # Check if this image has already been copied
          if image_file_abs in image_mapping:
            existing_file_id, existing_ext = image_mapping[image_file_abs]
            question_data_copy['has_image'] = True
            question_data_copy['image'] = f"imgs/{existing_file_id}{existing_ext}"

            print(f"Processed: {json_file_path.name} (Q{question_data.get('question', '?')}) -> {file_id}.txt, {file_id}.json, reusing image {existing_file_id}{existing_ext}")
          else:
            # Optimize image for API compliance (≤5 MB base64, ≤1568px)
            image_ext = ".jpg"  # optimizer always outputs JPEG
            image_filename = f"{file_id}{image_ext}"
            image_dest_path = imgs_dir / image_filename
            from questions.modules.services.image_optimizer import optimize_image_for_claude
            opt_result = optimize_image_for_claude(str(image_file), str(image_dest_path))
            if opt_result.get('optimized'):
              orig = opt_result['original']
              final = opt_result['final']
              print(f"  [optimized] {orig['base64_size_mb']:.1f}MB -> {final['base64_size_mb']:.1f}MB, "
                    f"{orig['width']}x{orig['height']} -> {final['width']}x{final['height']}, q={final['quality']}")

            # Track this image to avoid future duplicates
            image_mapping[image_file_abs] = (file_id, image_ext)

            question_data_copy['has_image'] = True
            question_data_copy['image'] = f"imgs/{file_id}{image_ext}"

            print(
              f"Processed: {json_file_path.name} (Q{question_data.get('question', '?')}) -> {file_id}.txt, {file_id}.json, {file_id}{image_ext}")
        else:
          # No image found
          question_data_copy['has_image'] = False
          question_data_copy['image'] = None

          print(
            f"Processed: {json_file_path.name} (Q{question_data.get('question', '?')}) -> {file_id}.txt, {file_id}.json (no image)")

        # Track first question of each type from myzanichelli for documentation
        if source_name == "myzanichelli" and question_type_val not in first_question_by_type:
          # Try to find the screenshot for this question
          exercise_num = question_data.get("exercise")
          question_num = question_data.get("question")

          if exercise_num is not None and question_num is not None:
            screenshot_path = Path(
              f"questions/myzanichelli/raw/{exercise_num}/screenshot/{question_num}.png")
            if screenshot_path.exists():
              # Copy screenshot to documentation folder
              doc_filename = f"{question_type_val}_example.png"
              doc_dest_path = documentation_dir / doc_filename
              shutil.copy2(screenshot_path, doc_dest_path)

              # Store info for README generation
              first_question_by_type[question_type_val] = {
                  'screenshot_path': f"documentation/{doc_filename}",
                  'file_id': file_id,
                  'exercise': exercise_num,
                  'question': question_num,
                  'source': f"{source_name}/{subfolder_name}"
              }

              print(
                f"  → Saved example screenshot for type '{question_type_val}' to {doc_dest_path}")

        # Save JSON file to metadata/ folder with normalized image fields
        json_filename = f"{file_id}.json"
        json_path = metadata_dir / json_filename
        with open(json_path, 'w', encoding='utf-8') as f:
          json.dump(question_data_copy, f, indent=2, ensure_ascii=False)

        processed_files.append(str(json_file_path))
        processed_metadata_files.append(str(json_path))

        if max_questions is not None and len(processed_metadata_files) >= max_questions:
          break

    except Exception as e:
      print(f"  Error processing {json_file_path}: {str(e)}")
      skipped_files.append(str(json_file_path))
      continue

  end_time = datetime.now()

  # Collect statistics
  stats = collect_statistics_from_metadata(processed_metadata_files)

  # Calculate version once for both files
  if version is None:
    if previous_version is not None:
      version = previous_version + REPORT_CONFIG['version_increment']
    else:
      version = REPORT_CONFIG['default_version']

  # Generate and write README.md
  report_content = generate_report(
      start_time, end_time, stats, dataset_dir, version, first_question_by_type)
  readme_file = dataset_path / REPORT_CONFIG['readme_filename']
  with open(readme_file, 'w', encoding='utf-8') as f:
    f.write(report_content)

  # Generate and write metadata.json
  metadata = generate_metadata(
      start_time, end_time, stats, dataset_dir, version)
  metadata_file = dataset_path / REPORT_CONFIG['metadata_filename']
  with open(metadata_file, 'w', encoding='utf-8') as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

  print(f"\n{'=' * 60}")
  print(f"Processing complete!")
  print(f"{'=' * 60}")
  print(f"Processed {len(set(processed_files))} source file(s)")
  print(f"Created {stats['total_questions']} question(s)")
  print(f"Skipped {len(skipped_files)} file(s)")
  print(f"Output directories:")
  print(f"  - Text files: {data_dir}")
  print(f"  - JSON metadata: {metadata_dir}")
  print(f"  - Images: {imgs_dir}")
  print(f"Duration: {(end_time - start_time).total_seconds():.2f} seconds")
  print(f"Reports generated:")
  print(f"  - README: {readme_file}")
  print(f"  - Metadata: {metadata_file}")

  # Print categorization summary
  if categorization_stats['attempted'] > 0:
    print(f"\nCategorization Summary:")
    print(f"  - Model: {categorization_model}")
    print(f"  - Attempted: {categorization_stats['attempted']}")
    print(f"  - Succeeded: {categorization_stats['succeeded']}")
    print(f"  - Failed: {categorization_stats['failed']}")
    total_cat_tokens = categorization_stats['total_input_tokens'] + categorization_stats['total_output_tokens']
    print(f"  - Total tokens: {total_cat_tokens:,} (input: {categorization_stats['total_input_tokens']:,}, output: {categorization_stats['total_output_tokens']:,})")
    print(f"  - Total processing time: {categorization_stats['total_processing_time']:.2f}s")
    if categorization_stats['succeeded'] > 0:
      avg_time = categorization_stats['total_processing_time'] / categorization_stats['attempted']
      print(f"  - Avg processing time: {avg_time:.2f}s per question")

  # Auto-run statistics
  run_statistics(dataset_path, metadata_dir, imgs_dir)


def run_statistics(dataset_path: Path, metadata_dir: Path, imgs_dir: Path):
  """Compute pre-experiment item-level statistics and generate paper-ready figures."""
  import csv as csv_mod
  import re as re_mod
  from collections import defaultdict as dd, Counter
  import numpy as np

  print(f"\n{'=' * 60}")
  print("Computing dataset statistics...")
  print(f"{'=' * 60}")

  stats_dir = dataset_path / "statistics"
  plots_dir = stats_dir / "plots"
  stats_dir.mkdir(parents=True, exist_ok=True)
  plots_dir.mkdir(parents=True, exist_ok=True)

  # --- Load metadata ---
  items = {}
  for f in sorted(metadata_dir.glob("*.json")):
    items[f.stem] = json.loads(f.read_text(encoding="utf-8"))
  n = len(items)
  print(f"  {n} questions loaded")

  def _write_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
      json.dump(data, fh, indent=2, ensure_ascii=False)

  def _write_csv(rows, path):
    if not rows: return
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", encoding="utf-8", newline="") as fh:
      w = csv_mod.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
      w.writeheader(); w.writerows(rows)

  # --- Pre-compute per-item features ---
  import tiktoken
  enc = tiktoken.get_encoding("cl100k_base")

  def _opt_texts(choices):
    texts = []
    if not choices: return texts
    for c in choices:
      if isinstance(c, dict):
        if "text" in c: texts.append(c["text"])
        elif "options" in c:
          for o in c["options"]: texts.append(str(o))
      elif isinstance(c, str): texts.append(c)
    return texts

  per_item = []
  for qid, m in items.items():
    qt = m.get("question_text") or ""
    ch = m.get("choices") or []
    ans = m.get("answers") or []
    ot = _opt_texts(ch)
    ol = [len(enc.encode(t)) for t in ot]
    n_correct = len(ans)
    per_item.append({
      "qid": qid, "type": m.get("type", "unknown"),
      "language": m.get("language", "unknown"),
      "has_image": bool(m.get("has_image")),
      "epistemic_level": m.get("epistemic_level") or "uncategorized",
      "cultural_tradition": m.get("cultural_tradition") or "uncategorized",
      "disciplinary_domain": m.get("disciplinary_domain") or "uncategorized",
      "q_tokens": len(enc.encode(qt)),
      "n_options": len(ol),
      "avg_option_tokens": float(np.mean(ol)) if ol else 0.0,
      "n_correct": n_correct,
    })

  # Convenience arrays
  types = [r["type"] for r in per_item]
  langs = [r["language"] for r in per_item]
  q_tokens = np.array([r["q_tokens"] for r in per_item])
  n_options = np.array([r["n_options"] for r in per_item])
  avg_opt = np.array([r["avg_option_tokens"] for r in per_item])
  n_correct = np.array([r["n_correct"] for r in per_item])
  has_image = np.array([r["has_image"] for r in per_item])
  epist = [r["epistemic_level"] for r in per_item]

  # --- Write per-item CSV ---
  _write_csv(per_item, stats_dir / "per_item_features.csv")
  _write_json(per_item, stats_dir / "per_item_features.json")

  # --- Compute summary statistics ---
  summary = {}

  # 1. Question type distribution
  type_counts = Counter(types)
  summary["question_type"] = {t: {"count": c, "pct": round(c / n * 100, 1)}
                               for t, c in sorted(type_counts.items(), key=lambda x: -x[1])}

  # 2. Language distribution
  lang_counts = Counter(langs)
  summary["language"] = {l: {"count": c, "pct": round(c / n * 100, 1)}
                          for l, c in sorted(lang_counts.items())}

  # 3. Question token count
  summary["question_tokens"] = {
    "mean": round(float(np.mean(q_tokens)), 1),
    "median": round(float(np.median(q_tokens)), 1),
    "std": round(float(np.std(q_tokens)), 1),
    "min": int(np.min(q_tokens)), "max": int(np.max(q_tokens)),
  }

  # 4. Number of answer options
  summary["n_options"] = {
    "mean": round(float(np.mean(n_options)), 1),
    "median": int(np.median(n_options)),
    "min": int(np.min(n_options)), "max": int(np.max(n_options)),
    "distribution": dict(sorted(Counter(n_options.tolist()).items())),
  }

  # 5. Average option length
  valid_opt = avg_opt[avg_opt > 0]
  summary["avg_option_length"] = {
    "mean": round(float(np.mean(valid_opt)), 1) if len(valid_opt) else 0,
    "std": round(float(np.std(valid_opt)), 1) if len(valid_opt) else 0,
  }

  # 6. Number of correct answers
  summary["n_correct"] = dict(sorted(Counter(n_correct.tolist()).items()))

  # 7. Epistemic level
  epist_counts = Counter(epist)
  summary["epistemic_level"] = {e: {"count": c, "pct": round(c / n * 100, 1)}
                                 for e, c in sorted(epist_counts.items())}

  # 8. Cultural tradition
  ct_counts = Counter(r["cultural_tradition"] for r in per_item)
  summary["cultural_tradition"] = {t: {"count": c, "pct": round(c / n * 100, 1)}
                                    for t, c in sorted(ct_counts.items(), key=lambda x: -x[1])}

  # 9. Disciplinary domain
  dd_counts = Counter(r["disciplinary_domain"] for r in per_item)
  summary["disciplinary_domain"] = {d: {"count": c, "pct": round(c / n * 100, 1)}
                                     for d, c in sorted(dd_counts.items(), key=lambda x: -x[1])}

  # 10. Image presence
  n_img = int(has_image.sum())
  summary["image_presence"] = {"with_image": n_img, "without_image": n - n_img}

  # Image properties
  from PIL import Image as PILImage
  img_data = []
  for qid, m in items.items():
    if not m.get("has_image"): continue
    ip = imgs_dir / f"{qid}.jpg"
    if not ip.exists(): continue
    try:
      img = PILImage.open(ip)
      w, h = img.size
      img_data.append({"qid": qid, "type": m.get("type", ""),
                        "width": w, "height": h, "resolution": w * h,
                        "file_size_kb": round(ip.stat().st_size / 1024, 1)})
    except: pass
  if img_data:
    widths = [d["width"] for d in img_data]
    heights = [d["height"] for d in img_data]
    resolutions = [d["resolution"] for d in img_data]
    filesizes = [d["file_size_kb"] for d in img_data]
    summary["image_properties"] = {
      "count": len(img_data),
      "width": {"mean": round(np.mean(widths), 0), "std": round(np.std(widths), 0)},
      "height": {"mean": round(np.mean(heights), 0), "std": round(np.std(heights), 0)},
      "resolution": {"mean": round(np.mean(resolutions), 0), "median": round(np.median(resolutions), 0)},
      "file_size_kb": {"mean": round(np.mean(filesizes), 1), "std": round(np.std(filesizes), 1)},
    }

  # 11. Structural complexity per type
  struct = {}
  _type_groups = dd(list)
  for r in per_item:
    _type_groups[r["type"]].append(r)
  for t, grp in sorted(_type_groups.items()):
    s = {"count": len(grp)}
    if t == "positioning":
      vals = [len(re_mod.findall(r"\[[A-Z]\]", items[r["qid"]].get("question_text", ""))) for r in grp]
      s["n_elements"] = {"mean": round(np.mean(vals), 1), "std": round(np.std(vals), 1)} if vals else {}
    elif t == "true_false":
      vals = [len(items[r["qid"]].get("choices") or []) for r in grp]
      s["n_statements"] = {"mean": round(np.mean(vals), 1), "std": round(np.std(vals), 1)} if vals else {}
    elif t == "completion_closed":
      vals = [sum(len(c.get("options", [])) if isinstance(c, dict) else 0
                  for c in (items[r["qid"]].get("choices") or [])) for r in grp]
      s["word_bank_size"] = {"mean": round(np.mean(vals), 1), "std": round(np.std(vals), 1)} if vals else {}
    struct[t] = s
  summary["structural_complexity"] = struct

  # 12. Cross-tabulations
  xtab_pairs = [
    ("type", "language"), ("type", "epistemic_level"),
    ("type", "has_image"), ("epistemic_level", "language"),
  ]
  cross_tabs = {}
  for a1, a2 in xtab_pairs:
    tab = dd(lambda: dd(int))
    for r in per_item:
      v1 = str(r[a1]); v2 = str(r[a2])
      tab[v1][v2] += 1
    cross_tabs[f"{a1}_x_{a2}"] = {k: dict(v) for k, v in sorted(tab.items())}
  summary["cross_tabulations"] = cross_tabs

  _write_json(summary, stats_dir / "summary.json")
  _write_csv(img_data, stats_dir / "image_properties.csv")

  # Print key stats
  print(f"  Types: {', '.join(f'{t}={c}' for t, c in type_counts.most_common())}")
  print(f"  Languages: {dict(lang_counts)}")
  print(f"  Tokens: mean={summary['question_tokens']['mean']}, median={summary['question_tokens']['median']}")
  print(f"  Images: {n_img}/{n}")

  # ===================================================================
  # PLOTS — organised as paper figures
  # ===================================================================
  import matplotlib
  matplotlib.use("Agg")
  import matplotlib.pyplot as plt
  from matplotlib.gridspec import GridSpec

  COLORS = plt.cm.Set2.colors

  # --- Fig 1: Dataset Overview (3 panels) ---
  fig = plt.figure(figsize=(16, 5))
  gs = GridSpec(1, 3, figure=fig, width_ratios=[2, 1, 1])

  # 1a. Question type distribution
  ax = fig.add_subplot(gs[0])
  t_sorted = sorted(type_counts.keys(), key=lambda x: type_counts[x])
  t_vals = [type_counts[t] for t in t_sorted]
  bars = ax.barh(t_sorted, t_vals, color=COLORS[:len(t_sorted)], edgecolor="black", linewidth=0.5)
  for bar, v in zip(bars, t_vals):
    ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2,
            f"{v} ({v/n*100:.0f}%)", va="center", fontsize=9)
  ax.set_xlabel("Count"); ax.set_title("(a) Question Type Distribution")

  # 1b. Language split
  ax = fig.add_subplot(gs[1])
  l_keys = sorted(lang_counts.keys())
  l_vals = [lang_counts[k] for k in l_keys]
  bars = ax.bar(l_keys, l_vals, color=[COLORS[0], COLORS[1]][:len(l_keys)], edgecolor="black", linewidth=0.5)
  for bar, v in zip(bars, l_vals):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
            f"{v}\n({v/n*100:.0f}%)", ha="center", fontsize=9)
  ax.set_ylabel("Count"); ax.set_title("(b) Language")

  # 1c. Image split
  ax = fig.add_subplot(gs[2])
  img_labels = ["With image", "Without"]
  img_vals = [n_img, n - n_img]
  bars = ax.bar(img_labels, img_vals, color=[COLORS[2], COLORS[3]], edgecolor="black", linewidth=0.5)
  for bar, v in zip(bars, img_vals):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
            f"{v}\n({v/n*100:.0f}%)", ha="center", fontsize=9)
  ax.set_ylabel("Count"); ax.set_title("(c) Image Presence")

  fig.tight_layout()
  fig.savefig(plots_dir / "fig1_dataset_overview.png", dpi=200)
  fig.savefig(plots_dir / "fig1_dataset_overview.pdf")
  plt.close(fig)

  # --- Fig 2: Question Length Analysis (3 panels) ---
  fig, axes_f2 = plt.subplots(1, 3, figsize=(16, 5))

  # 2a. Histogram with KDE
  ax = axes_f2[0]
  ax.hist(q_tokens, bins=30, edgecolor="black", alpha=0.7, density=True, color=COLORS[0])
  from scipy.stats import gaussian_kde
  if len(q_tokens[q_tokens > 0]) > 2:
    kde = gaussian_kde(q_tokens[q_tokens > 0])
    x_range = np.linspace(0, q_tokens.max(), 200)
    ax.plot(x_range, kde(x_range), color="red", linewidth=2)
  ax.axvline(np.mean(q_tokens), color="black", linestyle="--", alpha=0.7, label=f"Mean={np.mean(q_tokens):.0f}")
  ax.axvline(np.median(q_tokens), color="gray", linestyle=":", alpha=0.7, label=f"Median={np.median(q_tokens):.0f}")
  ax.legend(fontsize=8); ax.set_xlabel("Tokens"); ax.set_ylabel("Density")
  ax.set_title("(a) Token Count Distribution")

  # 2b. Box plots by type
  ax = axes_f2[1]
  type_order = sorted(set(types))
  type_data = [[q_tokens[i] for i in range(len(per_item)) if types[i] == t] for t in type_order]
  bp = ax.boxplot(type_data, tick_labels=type_order, patch_artist=True, showfliers=False)
  for patch, color in zip(bp["boxes"], COLORS):
    patch.set_facecolor(color)
  ax.set_ylabel("Tokens"); ax.set_title("(b) By Question Type")
  plt.sca(ax); plt.xticks(rotation=35, ha="right", fontsize=8)

  # 2c. Box plots by language
  ax = axes_f2[2]
  lang_order = sorted(set(langs))
  lang_data = [[q_tokens[i] for i in range(len(per_item)) if langs[i] == l] for l in lang_order]
  bp = ax.boxplot(lang_data, tick_labels=lang_order, patch_artist=True, showfliers=False)
  for patch, color in zip(bp["boxes"], COLORS):
    patch.set_facecolor(color)
  ax.set_ylabel("Tokens"); ax.set_title("(c) By Language")

  fig.tight_layout()
  fig.savefig(plots_dir / "fig2_question_length.png", dpi=200)
  fig.savefig(plots_dir / "fig2_question_length.pdf")
  plt.close(fig)

  # --- Fig 3: Answer Structure (3 panels) ---
  fig, axes_f3 = plt.subplots(1, 3, figsize=(16, 5))

  # 3a. Number of options — bar chart coloured by type
  ax = axes_f3[0]
  opt_by_type = dd(lambda: Counter())
  for r in per_item:
    opt_by_type[r["type"]][r["n_options"]] += 1
  all_opt_counts = sorted(set(r["n_options"] for r in per_item))
  bottom = np.zeros(len(all_opt_counts))
  for ti, t in enumerate(type_order):
    vals = [opt_by_type[t].get(oc, 0) for oc in all_opt_counts]
    ax.bar(range(len(all_opt_counts)), vals, bottom=bottom,
           label=t, color=COLORS[ti % len(COLORS)], edgecolor="black", linewidth=0.3)
    bottom += vals
  ax.set_xticks(range(len(all_opt_counts)))
  ax.set_xticklabels(all_opt_counts)
  ax.set_xlabel("Number of Options"); ax.set_ylabel("Count")
  ax.set_title("(a) Option Count by Type"); ax.legend(fontsize=6, ncol=2)

  # 3b. Average option length by type
  ax = axes_f3[1]
  opt_len_by_type = [[avg_opt[i] for i in range(len(per_item))
                       if types[i] == t and avg_opt[i] > 0] for t in type_order]
  opt_len_by_type_filtered = [(t, d) for t, d in zip(type_order, opt_len_by_type) if d]
  if opt_len_by_type_filtered:
    t_labels, t_data = zip(*opt_len_by_type_filtered)
    bp = ax.boxplot(t_data, tick_labels=t_labels, patch_artist=True, showfliers=False)
    for patch, color in zip(bp["boxes"], COLORS):
      patch.set_facecolor(color)
  ax.set_ylabel("Avg Option Tokens"); ax.set_title("(b) Option Length by Type")
  plt.sca(ax); plt.xticks(rotation=35, ha="right", fontsize=8)

  # 3c. Number of correct answers by type
  ax = axes_f3[2]
  corr_by_type = dd(lambda: Counter())
  for r in per_item:
    corr_by_type[r["type"]][r["n_correct"]] += 1
  all_corr = sorted(set(r["n_correct"] for r in per_item))
  bottom = np.zeros(len(all_corr))
  for ti, t in enumerate(type_order):
    vals = [corr_by_type[t].get(c, 0) for c in all_corr]
    ax.bar(range(len(all_corr)), vals, bottom=bottom,
           label=t, color=COLORS[ti % len(COLORS)], edgecolor="black", linewidth=0.3)
    bottom += vals
  ax.set_xticks(range(len(all_corr)))
  ax.set_xticklabels(all_corr)
  ax.set_xlabel("Correct Answers"); ax.set_ylabel("Count")
  ax.set_title("(c) Correct Answer Count by Type"); ax.legend(fontsize=6, ncol=2)

  fig.tight_layout()
  fig.savefig(plots_dir / "fig3_answer_structure.png", dpi=200)
  fig.savefig(plots_dir / "fig3_answer_structure.pdf")
  plt.close(fig)

  # --- Fig 4: Categorisation Axes (3 panels) ---
  fig, axes_f4 = plt.subplots(1, 3, figsize=(16, 5))

  # 4a. Epistemic level
  ax = axes_f4[0]
  ep_order = sorted(epist_counts.keys())
  ep_vals = [epist_counts[e] for e in ep_order]
  bars = ax.bar(ep_order, ep_vals, color=COLORS[:len(ep_order)], edgecolor="black", linewidth=0.5)
  for bar, v in zip(bars, ep_vals):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
            f"{v}\n({v/n*100:.0f}%)", ha="center", fontsize=9)
  ax.set_ylabel("Count"); ax.set_title("(a) Epistemic Level")

  # 4b. Cultural tradition (log scale for skewed data)
  ax = axes_f4[1]
  ct_order = sorted(ct_counts.keys(), key=lambda x: -ct_counts[x])
  ct_vals = [ct_counts[t] for t in ct_order]
  bars = ax.bar(ct_order, ct_vals, color=COLORS[:len(ct_order)], edgecolor="black", linewidth=0.5)
  for bar, v in zip(bars, ct_vals):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(ct_vals) * 0.02,
            str(v), ha="center", fontsize=9)
  if max(ct_vals) / max(min(v for v in ct_vals if v > 0), 1) > 10:
    ax.set_yscale("log")
  ax.set_ylabel("Count"); ax.set_title("(b) Cultural Tradition")
  plt.sca(ax); plt.xticks(rotation=20, ha="right", fontsize=8)

  # 4c. Disciplinary domain
  ax = axes_f4[2]
  dd_order = sorted(dd_counts.keys(), key=lambda x: -dd_counts[x])
  dd_vals = [dd_counts[d] for d in dd_order]
  bars = ax.bar(dd_order, dd_vals, color=COLORS[:len(dd_order)], edgecolor="black", linewidth=0.5)
  for bar, v in zip(bars, dd_vals):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
            f"{v}\n({v/n*100:.0f}%)", ha="center", fontsize=9)
  ax.set_ylabel("Count"); ax.set_title("(c) Disciplinary Domain")
  plt.sca(ax); plt.xticks(rotation=20, ha="right", fontsize=8)

  fig.tight_layout()
  fig.savefig(plots_dir / "fig4_categorisation.png", dpi=200)
  fig.savefig(plots_dir / "fig4_categorisation.pdf")
  plt.close(fig)

  # --- Fig 5: Image Properties (2 panels) ---
  if img_data:
    fig, axes_f5 = plt.subplots(1, 2, figsize=(12, 5))

    # 5a. Width vs height scatter, coloured by type
    ax = axes_f5[0]
    type_to_color = {t: COLORS[i % len(COLORS)] for i, t in enumerate(type_order)}
    for d in img_data:
      ax.scatter(d["width"], d["height"], c=[type_to_color.get(d["type"], "gray")],
                 alpha=0.5, s=15, edgecolors="none")
    # Legend
    from matplotlib.lines import Line2D
    handles = [Line2D([0], [0], marker='o', color='w', markerfacecolor=type_to_color.get(t, "gray"),
                       markersize=6, label=t) for t in type_order if any(d["type"] == t for d in img_data)]
    ax.legend(handles=handles, fontsize=7, ncol=2)
    ax.set_xlabel("Width (px)"); ax.set_ylabel("Height (px)")
    ax.set_title("(a) Image Dimensions by Type")

    # 5b. File size histogram
    ax = axes_f5[1]
    ax.hist([d["file_size_kb"] for d in img_data], bins=30, edgecolor="black", alpha=0.7, color=COLORS[0])
    ax.set_xlabel("File Size (KB)"); ax.set_ylabel("Count")
    ax.set_title("(b) Image File Size Distribution")

    fig.tight_layout()
    fig.savefig(plots_dir / "fig5_image_properties.png", dpi=200)
    fig.savefig(plots_dir / "fig5_image_properties.pdf")
    plt.close(fig)

  # --- Fig 6: Cross-Tabulation Heatmaps (4 panels) ---
  fig, axes_f6 = plt.subplots(2, 2, figsize=(14, 10))
  panel_labels = ["(a)", "(b)", "(c)", "(d)"]

  for idx, ((a1, a2), ax) in enumerate(zip(xtab_pairs, axes_f6.flat)):
    tab = cross_tabs[f"{a1}_x_{a2}"]
    row_keys = sorted(tab.keys())
    col_keys = sorted(set(c for row in tab.values() for c in row))
    matrix = np.array([[tab.get(r, {}).get(c, 0) for c in col_keys] for r in row_keys])

    im = ax.imshow(matrix, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(col_keys)))
    ax.set_xticklabels(col_keys, rotation=45, ha="right", fontsize=7)
    ax.set_yticks(range(len(row_keys)))
    ax.set_yticklabels(row_keys, fontsize=7)
    # Annotate cells
    for i in range(len(row_keys)):
      for j in range(len(col_keys)):
        v = matrix[i, j]
        color = "white" if v > matrix.max() * 0.6 else "black"
        ax.text(j, i, str(int(v)), ha="center", va="center", fontsize=7, color=color)
    ax.set_title(f"{panel_labels[idx]} {a1} x {a2}", fontsize=10)

  fig.tight_layout()
  fig.savefig(plots_dir / "fig6_cross_tabulations.png", dpi=200)
  fig.savefig(plots_dir / "fig6_cross_tabulations.pdf")
  plt.close(fig)

  # --- Fig S1 (supplementary): Structural Complexity ---
  # Small multiples for type-specific structural metrics
  struct_panels = []
  for t in type_order:
    grp = [r for r in per_item if r["type"] == t]
    if t == "positioning":
      vals = [len(re_mod.findall(r"\[[A-Z]\]", items[r["qid"]].get("question_text", ""))) for r in grp]
      if vals: struct_panels.append((t, "Elements to arrange", vals))
    elif t == "true_false":
      vals = [len(items[r["qid"]].get("choices") or []) for r in grp]
      if vals: struct_panels.append((t, "Statements", vals))
    elif t == "completion_closed":
      vals = [len(re_mod.findall(r"\[[A-Z]\]", items[r["qid"]].get("question_text", ""))) for r in grp]
      if vals: struct_panels.append((t, "Blanks", vals))
    elif t == "select_errors":
      vals = [len(items[r["qid"]].get("answers") or []) for r in grp]
      if vals: struct_panels.append((t, "Errors", vals))

  if struct_panels:
    n_panels = len(struct_panels)
    fig, axes_s = plt.subplots(1, n_panels, figsize=(4 * n_panels, 4))
    if n_panels == 1: axes_s = [axes_s]
    for ax, (t, ylabel, vals) in zip(axes_s, struct_panels):
      ax.hist(vals, bins=max(1, max(vals) - min(vals) + 1), edgecolor="black", alpha=0.7, color=COLORS[0])
      ax.set_xlabel(ylabel); ax.set_ylabel("Count"); ax.set_title(t)
    fig.tight_layout()
    fig.savefig(plots_dir / "fig_s1_structural_complexity.png", dpi=200)
    fig.savefig(plots_dir / "fig_s1_structural_complexity.pdf")
    plt.close(fig)

  # --- Fig S2 (supplementary): Epistemic x Token length + Image presence ---
  fig, axes_s2 = plt.subplots(1, 2, figsize=(12, 5))

  # 13. Token count by epistemic level
  ax = axes_s2[0]
  ep_data_order = sorted(set(epist))
  ep_tok_data = [[q_tokens[i] for i in range(len(per_item)) if epist[i] == e] for e in ep_data_order]
  if any(ep_tok_data):
    bp = ax.boxplot(ep_tok_data, tick_labels=ep_data_order, patch_artist=True, showfliers=False)
    for patch, color in zip(bp["boxes"], COLORS):
      patch.set_facecolor(color)
  ax.set_ylabel("Tokens"); ax.set_title("(a) Token Count by Epistemic Level")

  # 14. Image presence by type
  ax = axes_s2[1]
  img_by_type = dd(lambda: [0, 0])
  for r in per_item:
    img_by_type[r["type"]][0 if r["has_image"] else 1] += 1
  t_labels_img = sorted(img_by_type.keys())
  x = np.arange(len(t_labels_img))
  w = 0.35
  with_img = [img_by_type[t][0] for t in t_labels_img]
  without_img = [img_by_type[t][1] for t in t_labels_img]
  ax.bar(x - w / 2, with_img, w, label="With image", color=COLORS[2], edgecolor="black", linewidth=0.3)
  ax.bar(x + w / 2, without_img, w, label="Without image", color=COLORS[3], edgecolor="black", linewidth=0.3)
  ax.set_xticks(x); ax.set_xticklabels(t_labels_img, rotation=35, ha="right", fontsize=8)
  ax.set_ylabel("Count"); ax.set_title("(b) Image Presence by Type"); ax.legend(fontsize=8)

  fig.tight_layout()
  fig.savefig(plots_dir / "fig_s2_epistemic_image.png", dpi=200)
  fig.savefig(plots_dir / "fig_s2_epistemic_image.pdf")
  plt.close(fig)

  print(f"  Summary: {stats_dir / 'summary.json'}")
  print(f"  Plots:   {plots_dir}/ (fig1-fig6 + fig_s1, fig_s2)")


if __name__ == "__main__":
  main()
