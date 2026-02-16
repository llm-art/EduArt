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
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Add questions directory to path for shared modules
sys.path.insert(0, str(Path(__file__).parent / "questions"))

from modules.llm.factory import create_llm_provider
from modules.services.image_optimizer import optimize_image_for_claude, get_base64_size
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
              default=['multiple_choice_radio'],
              help='Question type(s) to include (can be specified multiple times). Default: multiple_choice_radio')
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

  # Track image optimization statistics
  image_optimization_stats = {
      'total_images': 0,
      'optimized_count': 0,
      'already_optimal_count': 0,
      'reused_count': 0,
      'total_original_tokens': 0,
      'total_final_tokens': 0,
      'total_tokens_saved': 0,
      'optimizations': []
  }

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
            # Reuse the existing image file
            existing_file_id, existing_ext = image_mapping[image_file_abs]
            question_data_copy['has_image'] = True
            question_data_copy['image'] = f"imgs/{existing_file_id}{existing_ext}"

            # Track reused image
            image_optimization_stats['reused_count'] += 1

            print(f"Processed: {json_file_path.name} (Q{question_data.get('question', '?')}) -> {file_id}.txt, {file_id}.json, reusing image {existing_file_id}{existing_ext}")
          else:
            # Optimize and copy image with same file_id as the text and json files
            # Always save as .jpg after optimization
            image_ext = ".jpg"
            image_filename = f"{file_id}{image_ext}"
            image_dest_path = imgs_dir / image_filename

            # Optimize image for Claude API
            optimization_result = optimize_image_for_claude(
              str(image_file), str(image_dest_path))

            # Track this image to avoid future duplicates
            image_mapping[image_file_abs] = (file_id, image_ext)

            # Set standardized fields pointing to dataset/imgs
            question_data_copy['has_image'] = True
            question_data_copy['image'] = f"imgs/{file_id}{image_ext}"

            # Track image optimization statistics
            image_optimization_stats['total_images'] += 1

            # Add optimization info to metadata
            if optimization_result.get('optimized'):
              question_data_copy['image_optimization'] = {
                  'optimized': True,
                  'original_tokens': optimization_result['original']['tokens'],
                  'final_tokens': optimization_result['final']['tokens'],
                  'tokens_saved': optimization_result['savings']['tokens_saved'],
                  'tokens_saved_percent': optimization_result['savings']['tokens_percent']
              }

              # Track optimization stats
              image_optimization_stats['optimized_count'] += 1
              image_optimization_stats['total_original_tokens'] += optimization_result['original']['tokens']
              image_optimization_stats['total_final_tokens'] += optimization_result['final']['tokens']
              image_optimization_stats['total_tokens_saved'] += optimization_result['savings']['tokens_saved']

              # Record individual optimization
              image_optimization_stats['optimizations'].append({
                  'file_id': file_id,
                  'source_file': str(image_file),
                  'original_dimensions': f"{optimization_result['original']['width']}x{optimization_result['original']['height']}",
                  'final_dimensions': f"{optimization_result['final']['width']}x{optimization_result['final']['height']}",
                  'original_tokens': optimization_result['original']['tokens'],
                  'final_tokens': optimization_result['final']['tokens'],
                  'tokens_saved': optimization_result['savings']['tokens_saved'],
                  'tokens_saved_percent': optimization_result['savings']['tokens_percent'],
                  'original_size_mb': optimization_result['original']['base64_size_mb'],
                  'final_size_mb': optimization_result['final']['base64_size_mb'],
                  'quality': optimization_result['final']['quality']
              })

              opt_info = f" (optimized: {optimization_result['savings']['tokens_percent']:+.0f}% tokens)"
            elif optimization_result.get('already_optimal'):
              question_data_copy['image_optimization'] = {
                  'optimized': False,
                  'already_optimal': True,
                  'tokens': optimization_result['original_tokens']
              }

              # Track already optimal
              image_optimization_stats['already_optimal_count'] += 1
              image_optimization_stats['total_original_tokens'] += optimization_result['original_tokens']
              image_optimization_stats['total_final_tokens'] += optimization_result['original_tokens']

              # Add to optimizations list for logging (even though not optimized)
              # Get image info for already optimal images
              try:
                img = Image.open(str(image_file))
                width, height = img.size
                file_size = os.path.getsize(str(image_file))
                base64_size = get_base64_size(str(image_file))

                image_optimization_stats['optimizations'].append({
                    'file_id': file_id,
                    'source_file': str(image_file),
                    'final_dimensions': f"{width}x{height}",
                    'final_tokens': optimization_result['original_tokens'],
                    'final_size_mb': round(base64_size / 1024 / 1024, 2),
                    'quality': 'original'
                })
              except:
                pass

              opt_info = " (already optimal)"
            else:
              opt_info = ""

            print(
              f"Processed: {json_file_path.name} (Q{question_data.get('question', '?')}) -> {file_id}.txt, {file_id}.json, {file_id}{image_ext}{opt_info}")
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

  # Generate and write image optimization log as text file
  if image_optimization_stats['total_images'] > 0:
    optimization_log_file = dataset_path / 'image_optimization.log'

    with open(optimization_log_file, 'w', encoding='utf-8') as f:
      f.write("IMAGE OPTIMIZATION LOG\n")
      f.write("=" * 110 + "\n")
      f.write(f"Generated: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
      f.write(
        f"Total images processed: {image_optimization_stats['total_images']}\n")
      f.write(
        f"Optimized: {image_optimization_stats['optimized_count']} | Already optimal: {image_optimization_stats['already_optimal_count']}\n")
      f.write("=" * 110 + "\n\n")

      # Write table header
      f.write(f"{'Filename':<20} {'Dimensions':<18} {'Aspect Ratio':<15} {'MP':<8} {'Base64 Size (MB)':<18} {'Quality':<8}\n")
      f.write("-" * 110 + "\n")

      # Collect all image data (both optimized and already optimal)
      all_image_data = []

      # Add optimized images
      for opt in image_optimization_stats['optimizations']:
        all_image_data.append({
            'file_id': opt['file_id'],
            'dimensions': opt['final_dimensions'],
            'base64_size': opt['final_size_mb'],
            'tokens': opt['final_tokens'],
            'quality': opt.get('quality', 'N/A')
        })

      # Sort by file_id
      all_image_data.sort(key=lambda x: x['file_id'])

      # Write all image details
      for img_data in all_image_data:
        file_id = img_data['file_id']
        dimensions = img_data['dimensions']

        # Calculate aspect ratio from dimensions
        try:
          width, height = map(int, dimensions.split('x'))
          aspect_ratio = round(width / height, 2)
          mp = (width * height) / 1_000_000
        except:
          aspect_ratio = "N/A"
          mp = 0.0

        base64_size = img_data['base64_size']
        quality = img_data['quality']

        f.write(
          f"{file_id:<20} {dimensions:<18} {str(aspect_ratio):<15} {mp:<8.2f} {base64_size:<18.2f} {str(quality):<8}\n")

      f.write("\n" + "=" * 110 + "\n")
      f.write(f"Total: {len(all_image_data)} images\n")

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

  # Print image optimization summary
  if image_optimization_stats['total_images'] > 0:
    print(f"\nImage Optimization Summary:")
    print(
      f"  - Total images processed: {image_optimization_stats['total_images']}")
    print(f"  - Optimized: {image_optimization_stats['optimized_count']}")
    print(
      f"  - Already optimal: {image_optimization_stats['already_optimal_count']}")
    print(
      f"  - Reused (duplicates): {image_optimization_stats['reused_count']}")
    if image_optimization_stats['total_tokens_saved'] > 0:
      tokens_saved_pct = round(
        (image_optimization_stats['total_tokens_saved'] / image_optimization_stats['total_original_tokens'] * 100), 1)
      print(
        f"  - Tokens saved: {image_optimization_stats['total_tokens_saved']:,} ({tokens_saved_pct}%)")
      original_cost = image_optimization_stats['total_original_tokens'] / \
          image_optimization_stats['total_images'] * 1000 * 3.0 / 1_000_000
      final_cost = image_optimization_stats['total_final_tokens'] / \
          image_optimization_stats['total_images'] * 1000 * 3.0 / 1_000_000
      print(
        f"  - Cost savings: ${original_cost - final_cost:.2f} per 1K images")
    if image_optimization_stats['optimizations']:
      optimization_log_file = dataset_path / 'image_optimization.log'
      print(f"  - Optimization log: {optimization_log_file}")

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


if __name__ == "__main__":
  main()
