#!/usr/bin/env python3
"""
Dataset Bundler Script

This script reads JSON files from output/{exercise_number}/json/ directories,
extracts question data to create TXT files, copies JSON files to metadata/, 
and copies associated images to imgs/ folder with consistent naming.
"""

import os
import json
import glob
import shutil
import re
import click
from datetime import datetime
from pathlib import Path
from collections import defaultdict


# Report configuration - single point for modifications
REPORT_CONFIG = {
    'readme_filename': 'README.md',
    'metadata_filename': 'metadata.json',
    'default_version': 0.1,
    'version_increment': 0.1,
    'sections': [
        'creation_datetime',
        'processing_time',
        'version',
        'exercise_count',
        'question_count',
        'questions_with_images',
        'questions_by_type',
        'ai_calls_summary',
        'cost_analysis'
    ],
    'pricing': {
        'Google gemini-2.5-flash-lite': {
            'input_cost_per_million': 0.1,  # $0.1 per 1M input tokens
            'output_cost_per_million': 0.4  # $0.4 per 1M output tokens
        }
    }
}


def find_json_files(base_path="output"):
  """Find all JSON files in output/{exercise_number}/json/ directories."""
  json_files = []

  # Check if we're in the questions directory or parent directory
  if os.path.exists("questions/myzanichelli/structured"):
    base_path = "questions/myzanichelli/structured"
  elif os.path.exists("structured"):
    base_path = "structured"
  else:
    print(f"Warning: Neither 'structured' nor 'questions/myzanichelli/structured' directory found")
    return []

  pattern = os.path.join(base_path, "*/json/*.json")

  for json_file in glob.glob(pattern):
    json_files.append(json_file)

  # Sort numerically by exercise number and question number
  def sort_key(filepath):
    # Extract exercise and question numbers from path like "output/1/json/5.json"
    parts = filepath.split(os.sep)
    exercise_num = int(parts[-3])  # exercise number
    question_num = int(os.path.splitext(parts[-1])[0])  # question number
    return (exercise_num, question_num)

  return sorted(json_files, key=sort_key)


def should_skip_question(json_data):
  """Check if a question should be skipped based on certain criteria."""
  # Currently not skipping any questions - we post-process them instead
  return False


def post_process_questions(json_data):
  """Post-process questions to fix wrong answers and normalize answer structures."""
  question_type = json_data.get("type")

  if question_type == "true_false":
    json_data = post_process_true_false(json_data)
  elif question_type == "multiple_choice_check":
    json_data = post_process_multiple_choice_check(json_data)
  
  # Normalize answer structures for consistent evaluation
  json_data = normalize_answers(json_data)

  return json_data


def post_process_true_false(json_data):
  """Post-process true_false questions to fix wrong answers and translate to Italian."""
  answers = json_data.get("answers", [])
  modified = False
  translated = False

  for answer in answers:
    if isinstance(answer, dict):
      current_text = answer.get("text", "")
      
      # First, translate English to Italian if needed
      if current_text.lower() in ["true", "vero"]:
        answer["text"] = "Vero"
        if current_text.lower() == "true":
          translated = True
      elif current_text.lower() in ["false", "falso"]:
        answer["text"] = "Falso"
        if current_text.lower() == "false":
          translated = True
      
      # Then, check for wrong answers and flip if needed
      note = answer.get("note", "")
      if "risposta sbagliata" in note.lower():
        # Flip the True/False value
        if answer["text"] == "Vero":
          answer["text"] = "Falso"
        elif answer["text"] == "Falso":
          answer["text"] = "Vero"
        modified = True

      # Remove note field
      if "note" in answer:
        del answer["note"]

  if translated:
    print(f"  Post-processed true_false question: translated English to Italian")
  if modified:
    print(f"  Post-processed true_false question: flipped wrong answers")

  return json_data


def post_process_multiple_choice_check(json_data):
  """Post-process multiple_choice_check questions to fix wrong answers."""
  answers = json_data.get("answers", [])
  modified = False

  for answer in answers:
    if isinstance(answer, dict):
      description = answer.get("description", "")
      if "risposta sbagliata" in description.lower():
        # Change description to correct answer
        answer["description"] = "Risposta esatta."
        modified = True

  if modified:
    print(f"  Post-processed multiple_choice_check question: fixed wrong answers")

  return json_data


def normalize_answers(json_data):
  """
  Normalize answer structures for consistent evaluation.
  
  This function standardizes answer formats across different question types:
  - Normalizes IDs to UPPERCASE
  - Normalizes text content to lowercase
  - Standardizes field names to 'text' for all text-based comparisons
  - Generates alphabetical IDs (A, B, C, ...) where missing
  
  Args:
      json_data: Question data dictionary
      
  Returns:
      Modified json_data with normalized answers
  """
  question_type = json_data.get("type")
  answers = json_data.get("answers", [])
  
  if not answers:
    return json_data
  
  # Helper function to generate alphabetical IDs
  def get_alpha_id(index):
    """Convert index to alphabetical ID (0->A, 1->B, ..., 25->Z, 26->AA, ...)"""
    result = ""
    while index >= 0:
      result = chr(65 + (index % 26)) + result
      index = index // 26 - 1
    return result
  
  # Normalize IDs to uppercase for ID-based questions
  # Remove description/text fields as they're not needed for evaluation
  if question_type in ["multiple_choice_radio", "multiple_choice_check"]:
    for answer in answers:
      if isinstance(answer, dict) and 'id' in answer:
        answer['id'] = answer['id'].strip().upper()
        # Remove text/description fields - only ID matters for these types
        answer.pop('text', None)
        answer.pop('description', None)
  
  # Normalize ID+text for text-based questions with existing IDs
  elif question_type in ["completion_closed", "positioning"]:
    for answer in answers:
      if isinstance(answer, dict):
        if 'id' in answer:
          answer['id'] = answer['id'].strip().upper()
        if 'description' in answer:
          # Standardize to 'text' field and normalize to lowercase
          answer['text'] = answer['description'].strip().lower()
          # Remove description field - only 'text' should remain
          del answer['description']
  
  elif question_type == "true_false":
    for answer in answers:
      if isinstance(answer, dict):
        if 'id' in answer:
          answer['id'] = answer['id'].strip().upper()
        if 'text' in answer:
          # Keep Italian text as-is (Vero/Falso), just strip whitespace
          # Don't convert to lowercase to preserve proper Italian capitalization
          answer['text'] = answer['text'].strip()
        # Remove description field if present
        answer.pop('description', None)
  
  elif question_type == "select_errors":
    # Transform from {correct, error} to {id, text} format
    # Generate alphabetical IDs (A, B, C, ...)
    normalized = []
    for idx, answer in enumerate(answers):
      if isinstance(answer, dict):
        normalized.append({
            'id': get_alpha_id(idx),
            'text': answer.get('error', '').strip().lower()
        })
    json_data['answers'] = normalized
    print(f"  Normalized select_errors: generated {len(normalized)} alphabetical IDs")
  
  elif question_type == "completion_open":
    # Transform from list of strings to list of {id, text} dicts
    # Extract IDs from question_text placeholders [A], [B], [C], etc.
    question_text = json_data.get("question_text", "")
    
    # Find all placeholders like [A], [B], [C] in order
    placeholders = re.findall(r'\[([A-Z]+)\]', question_text)
    
    if isinstance(answers[0], str):
      normalized = []
      for idx, answer_text in enumerate(answers):
        # Use placeholder ID if available, otherwise generate alphabetical ID
        if idx < len(placeholders):
          answer_id = placeholders[idx].strip().upper()
        else:
          answer_id = get_alpha_id(idx)
        
        normalized.append({
            'id': answer_id,
            'text': answer_text.strip().lower()
        })
      json_data['answers'] = normalized
      print(f"  Normalized completion_open: extracted {len(placeholders)} IDs from placeholders, generated {len(normalized)} total")
  
  return json_data


def find_associated_image(json_file, json_data=None):
  """Find associated image file for a JSON file by checking has_image field."""
  # If json_data is not provided, read it from the file
  if json_data is None:
    try:
      with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    except Exception as e:
      print(f"Warning: Could not read JSON file {json_file}: {e}")
      return None

  # Check if the question has an image
  has_image = json_data.get("has_image", False)
  if not has_image:
    return None

  # Get the image path from the JSON data
  image_path = json_data.get("image", "")
  if image_path and os.path.exists(image_path):
    return image_path

  # Fallback: try to find image using the old method if image path doesn't exist
  path_parts = json_file.split(os.sep)
  exercise_num = path_parts[-3]  # exercise number
  # question number without .json
  question_num = os.path.splitext(path_parts[-1])[0]

  # Look for images in data/{exercise_num}/raw/ and data/{exercise_num}/imgs/
  image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']

  # Determine the correct data path
  data_base = "raw"
  if os.path.exists("questions/myzanichelli/raw"):
    data_base = "questions/myzanichelli/raw"

  # Check imgs folder first (processed images)
  imgs_folder = os.path.join(data_base, exercise_num, "imgs")
  if os.path.exists(imgs_folder):
    for ext in image_extensions:
      fallback_path = os.path.join(imgs_folder, f"{question_num}{ext}")
      if os.path.exists(fallback_path):
        return fallback_path

  # Check screenshot folder as fallback
  screenshot_folder = os.path.join(data_base, exercise_num, "screenshot")
  if os.path.exists(screenshot_folder):
    for ext in image_extensions:
      fallback_path = os.path.join(screenshot_folder, f"{question_num}{ext}")
      if os.path.exists(fallback_path):
        return fallback_path

  return None


def extract_question_data(json_data):
  """Extract question title, text, choices, and type from JSON data."""
  question_title = json_data.get("question_title", "")
  question_text = json_data.get("question_text", "")
  question_type = json_data.get("type", "")
  choices = json_data.get("choices", [])

  # Handle different choice formats
  formatted_choices = []
  if choices is None:
    # No choices available
    pass
  elif isinstance(choices, list) and len(choices) > 0:
    if isinstance(choices[0], dict):
      # Check if it's the standard format with "text" field
      if "text" in choices[0]:
        # Format: [{"id": "A", "text": "...", "is_correct": ...}, ...]
        for choice in choices:
          if isinstance(choice, dict):
            choice_id = choice.get("id", "")
            choice_text = choice.get("text", "")
            if choice_id and choice_text:
              formatted_choices.append(f"{choice_id}. {choice_text}")
      elif "options" in choices[0]:
        # Format: [{"id": "BLANK_1", "options": ["option1", "option2"]}, ...]
        for choice in choices:
          if isinstance(choice, dict):
            choice_id = choice.get("id", "")
            options = choice.get("options", [])
            if choice_id and options:
              formatted_choices.append(f"{choice_id}:")
              for i, option in enumerate(options, 1):
                formatted_choices.append(f"  {i}. {option}")
    elif isinstance(choices[0], str):
      # Format: ["option1", "option2", ...]
      for i, choice_text in enumerate(choices, 1):
        if choice_text:
          formatted_choices.append(f"{i}. {choice_text}")

  return question_title, question_text, formatted_choices, question_type


def get_question_type_text(question_type):
  """Get the instruction text based on question type."""
  type_texts = {
      "multiple_choice_radio": "SCELTA MULTIPLA\n**Cosa devi fare:** scegli la risposta esatte tra quelle proposte",
      "multiple_choice_check": "SCELTA MULTIPLA\n**Cosa devi fare:** scegli tutte le risposte esatta tra quelle proposte",
      "true_false": "VERO O FALSO\n**Cosa devi fare:** vero o falso? Scegli la risposta esatta",
      "completion_open": "COMPLETAMENTO APERTO\n**Cosa devi fare**: completa l'esercizio con le risposte che ti sembrano esatte",
      "positioning": "POSIZIONAMENTO\n**Cosa devi fare**: completa le parti mancanti dell'esercizio con le alternative proposte",
      "completion_closed": "COMPLETAMENTO CHIUSO\n**Cosa devi fare**: scegli la risposta esatta per ogni gruppo di opzioni proposte",
      "select_errors": "TROVA ERRORE\n**Cosa devi fare**: seleziona le parti di testo che ritieni sbagliate. Controlla il contatore per verificare di aver selezionato il numero giusto di errori"
  }
  return type_texts.get(question_type, "")


def create_txt_content(question_title, question_text, choices, question_type=""):
  """Create the content for the TXT file."""
  content = []

  if question_title:
    content.append(f"Title: {question_title}")
    content.append("")

  # Add question type instructions
  type_text = get_question_type_text(question_type)
  if type_text:
    content.append(type_text)
    content.append("")

  if question_text:
    content.append(f"Question: {question_text}")
    content.append("")

  if choices:
    content.append("Choices:")
    for choice in choices:
      content.append(choice)

  return "\n".join(content)


def get_next_file_id(data_dir):
  """Get the next available 4-digit file identifier."""
  existing_files = glob.glob(os.path.join(data_dir, "*.txt"))

  if not existing_files:
    return "0001"

  # Extract numbers from existing files
  numbers = []
  for file_path in existing_files:
    filename = os.path.basename(file_path)
    if filename.endswith(".txt") and len(filename) == 8:  # XXXX.txt
      try:
        num = int(filename[:4])
        numbers.append(num)
      except ValueError:
        continue

  if numbers:
    next_num = max(numbers) + 1
  else:
    next_num = 1

  return f"{next_num:04d}"


def update_metadata(metadata_file, processed_files, start_time, end_time):
  """Create or update the metadata file."""
  metadata = {
      "last_updated": end_time.isoformat(),
      "processing_sessions": []
  }

  # Load existing metadata if file exists
  if os.path.exists(metadata_file):
    try:
      with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
      pass

  # Add new processing session
  session = {
      "timestamp": start_time.isoformat(),
      "duration_seconds": (end_time - start_time).total_seconds(),
      "files_processed": len(processed_files),
      "source_files": processed_files
  }

  metadata["processing_sessions"].append(session)
  metadata["last_updated"] = end_time.isoformat()

  # Count total files in data directory
  data_dir = os.path.join(os.path.dirname(metadata_file), "..", "data")
  metadata["total_files"] = len(glob.glob(os.path.join(data_dir, "*.txt")))

  # Write updated metadata
  with open(metadata_file, 'w', encoding='utf-8') as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)


def get_previous_version(dataset_dir):
  """Get version from previous metadata file, if it exists."""
  # Convert to absolute path to handle relative paths correctly
  dataset_path = Path(dataset_dir).resolve()

  # Check if dataset directory exists
  if not dataset_path.exists():
    return None

  # Try to get version from metadata.json first (more reliable)
  metadata_file = dataset_path / REPORT_CONFIG['metadata_filename']
  if metadata_file.exists() and metadata_file.is_file():
    try:
      with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
        return metadata.get('version')
    except Exception as e:
      print(
        f"Warning: Could not read previous version from {metadata_file}: {e}")

  # Fallback to README.md
  readme_file = dataset_path / REPORT_CONFIG['readme_filename']
  if readme_file.exists() and readme_file.is_file():
    try:
      with open(readme_file, 'r', encoding='utf-8') as f:
        content = f.read()
        # Look for version line in format "**Version:** X.X"
        version_match = re.search(r'\*\*Version:\*\* (\d+\.\d+)', content)
        if version_match:
          return float(version_match.group(1))
    except Exception as e:
      print(
        f"Warning: Could not read previous version from {readme_file}: {e}")

  return None


def collect_statistics_from_metadata(metadata_files, imgs_dir):
  """Collect statistics about the dataset from processed metadata files."""
  stats = {
      'exercises': set(),
      'total_questions': len(metadata_files),
      'questions_with_images': 0,
      'questions_by_type': defaultdict(int),
      'ai_calls': {}
  }

  # Count questions with images
  if os.path.exists(imgs_dir):
    image_files = glob.glob(os.path.join(imgs_dir, "*"))
    stats['questions_with_images'] = len(image_files)

  # Process each metadata JSON file to get exercise numbers, question types, and AI calls
  for json_file in metadata_files:
    try:
      # Read JSON to get question type and extract exercise info
      with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        question_type = json_data.get("type", "unknown")
        stats['questions_by_type'][question_type] += 1

        # Try to extract exercise number from source file path if available
        source_file = json_data.get("source_file", "")
        if source_file:
          path_parts = source_file.split(os.sep)
          if len(path_parts) >= 3:
            exercise_num = path_parts[-3]  # exercise number
            stats['exercises'].add(exercise_num)

        # Process AI calls
        ai_calls = json_data.get("ai_calls", [])
        for ai_call in ai_calls:
          description = ai_call.get("description", "unknown")
          model_name = ai_call.get("model_name", "unknown")

          # Create a unique key for this AI call type
          call_key = f"{description}_{model_name}"

          if call_key not in stats['ai_calls']:
            stats['ai_calls'][call_key] = {
                'description': description,
                'model_name': model_name,
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'processing_time': 0.0,
                'call_count': 0
            }

          # Aggregate the numeric values
          stats['ai_calls'][call_key]['input_tokens'] += ai_call.get(
            'input_tokens', 0)
          stats['ai_calls'][call_key]['output_tokens'] += ai_call.get(
            'output_tokens', 0)
          stats['ai_calls'][call_key]['total_tokens'] += ai_call.get(
            'total_tokens', 0)
          stats['ai_calls'][call_key]['processing_time'] += ai_call.get(
            'processing_time', 0.0)
          stats['ai_calls'][call_key]['call_count'] += 1

    except Exception as e:
      print(f"Warning: Could not process statistics for {json_file}: {e}")
      continue

  # If we couldn't extract exercise numbers from metadata, try to infer from original structure
  if not stats['exercises']:
    # Look for original JSON files to count exercises
    json_files = find_json_files()
    for json_file in json_files:
      try:
        path_parts = json_file.split(os.sep)
        exercise_num = path_parts[-3]  # exercise number
        stats['exercises'].add(exercise_num)
      except Exception:
        continue

  return stats


def calculate_ai_costs(stats):
  """Calculate the total cost of AI calls based on token usage and pricing."""
  total_cost = 0.0
  cost_breakdown = {}

  for call_data in stats['ai_calls'].values():
    model_name = call_data['model_name']
    input_tokens = call_data['input_tokens']
    output_tokens = call_data['output_tokens']

    # Get pricing for this model (default to 0 if not found)
    pricing = REPORT_CONFIG['pricing'].get(model_name, {
        'input_cost_per_million': 0.0,
        'output_cost_per_million': 0.0
    })

    # Calculate costs (convert tokens to millions)
    input_cost = (input_tokens / 1_000_000) * pricing['input_cost_per_million']
    output_cost = (output_tokens / 1_000_000) * \
        pricing['output_cost_per_million']
    call_cost = input_cost + output_cost

    cost_breakdown[f"{call_data['description']} ({model_name})"] = {
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'input_cost': input_cost,
        'output_cost': output_cost,
        'total_cost': call_cost
    }

    total_cost += call_cost

  return total_cost, cost_breakdown


def generate_report(start_time, end_time, stats, dataset_dir, version):
  """Generate the dataset bundle report in markdown format."""
  # Calculate processing time
  processing_time = end_time - start_time

  # Calculate AI costs
  total_cost, cost_breakdown = calculate_ai_costs(stats)

  # Generate report content
  report_content = f"""# Dataset Bundle Report

**Creation Date & Time:** {start_time.strftime('%Y-%m-%d %H:%M:%S')}

**Processing Time:** {processing_time.total_seconds():.2f} seconds

**Version:** {version:.1f}

**Number of Exercises:** {len(stats['exercises'])}

**Number of Questions:** {stats['total_questions']}

**Number of Questions with Images:** {stats['questions_with_images']}

**Total Cost:** ${total_cost:.4f}

## Questions by Type

"""

  # Add questions by type section
  for question_type, count in sorted(stats['questions_by_type'].items()):
    report_content += f"- **{question_type}:** {count}\n"

  # Add AI calls section
  if stats['ai_calls']:
    report_content += f"""
## AI Calls Summary

"""
    for call_data in stats['ai_calls'].values():
      report_content += f"""### {call_data['description'].title()}
- **Model:** {call_data['model_name']}
- **Input Tokens:** {call_data['input_tokens']:,}
- **Output Tokens:** {call_data['output_tokens']:,}
- **Total Tokens:** {call_data['total_tokens']:,}
- **Processing Time:** {call_data['processing_time']:.2f} seconds

"""

  # Add cost breakdown section
  if cost_breakdown:
    report_content += f"""
## Cost Breakdown

"""
    for call_type, cost_data in cost_breakdown.items():
      report_content += f"""### {call_type}
- **Input Tokens:** {cost_data['input_tokens']:,} (${cost_data['input_cost']:.4f})
- **Output Tokens:** {cost_data['output_tokens']:,} (${cost_data['output_cost']:.4f})
- **Total Cost:** ${cost_data['total_cost']:.4f}

"""

    report_content += f"**Grand Total:** ${total_cost:.4f}\n"

  report_content += f"""
---
*Report generated automatically by dataset bundler script*
*Last updated: {end_time.strftime('%Y-%m-%d %H:%M:%S')}*
"""

  return report_content


def generate_metadata(start_time, end_time, stats, dataset_dir, version):
  """Generate the dataset bundle metadata in JSON format."""
  # Calculate processing time
  processing_time = end_time - start_time

  # Convert AI calls dictionary to list format for JSON
  ai_calls_list = []
  for call_data in stats['ai_calls'].values():
    ai_calls_list.append({
        "description": call_data['description'],
        "model_name": call_data['model_name'],
        "input_tokens": call_data['input_tokens'],
        "output_tokens": call_data['output_tokens'],
        "total_tokens": call_data['total_tokens'],
        "processing_time": call_data['processing_time']
    })

  # Generate metadata structure
  metadata = {
      "creation_datetime": start_time.strftime('%Y-%m-%d %H:%M:%S'),
      "processing_time_seconds": processing_time.total_seconds(),
      "version": version,
      "exercise_count": len(stats['exercises']),
      "question_count": stats['total_questions'],
      "questions_with_images": stats['questions_with_images'],
      "questions_by_type": dict(stats['questions_by_type']),
      "exercises": sorted(list(stats['exercises'])),
      "ai_calls": ai_calls_list,
      "last_updated": end_time.strftime('%Y-%m-%d %H:%M:%S')
  }

  return metadata


def copy_preprocessed_images(dataset_dir, processed_metadata_files):
  """
  Optional function to copy images with 'pre_' prefix from raw/ folders
  to dataset/raw/ with sequential IDs matching the main dataset processing.
  """
  # Determine the correct data path
  data_base = "raw"
  if os.path.exists("questions/myzanichelli/raw"):
    data_base = "questions/myzanichelli/raw"

  if not os.path.exists(data_base):
    print(f"Warning: Data directory '{data_base}' not found")
    return

  # Create dataset/raw directory if it doesn't exist
  dataset_raw_dir = os.path.join(dataset_dir, "raw")
  os.makedirs(dataset_raw_dir, exist_ok=True)

  copied_count = 0
  image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']

  # Process metadata files in the same order as main processing
  for metadata_file in processed_metadata_files:
    try:
      # Read the metadata to get exercise and question info
      with open(metadata_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

      # Get the file ID from the metadata filename (e.g., "0001.json" -> "0001")
      metadata_filename = os.path.basename(metadata_file)
      file_id = os.path.splitext(metadata_filename)[0]

      # Extract exercise and question numbers from the metadata
      exercise_num = json_data.get("exercise")
      question_num = json_data.get("question")

      if exercise_num is None or question_num is None:
        continue

      # Look for preprocessed image in screenshot folder
      screenshot_folder = os.path.join(data_base, str(exercise_num), "screenshot")
      if not os.path.exists(screenshot_folder):
        continue

      # Try to find the preprocessed image
      found_image = None
      for ext in image_extensions:
        pre_image_path = os.path.join(screenshot_folder, f"pre_{question_num}{ext}")
        if os.path.exists(pre_image_path):
          found_image = pre_image_path
          break

      if found_image:
        # Get the extension from the found image
        image_ext = os.path.splitext(found_image)[1]
        # Copy to dataset/raw/ with sequential ID
        dest_filename = f"{file_id}{image_ext}"
        dest_path = os.path.join(dataset_raw_dir, dest_filename)
        shutil.copy2(found_image, dest_path)
        print(f"Copied preprocessed image: {found_image} -> {dest_path}")
        copied_count += 1

    except Exception as e:
      print(
        f"Warning: Could not process preprocessed image for {metadata_file}: {e}")
      continue

  if copied_count > 0:
    print(f"Copied {copied_count} preprocessed images to {dataset_raw_dir}")
  else:
    print("No preprocessed images with 'pre_' prefix found")


@click.command()
@click.option('--version', type=float, help='Specify version number for the report')
@click.option('--copy-preprocessed', is_flag=True, help='Copy images with pre_ prefix from raw/ folders')
@click.option('--output-dir', default='dataset', help='Output directory for the dataset (default: dataset)')
def main(version, copy_preprocessed, output_dir):
  """Main function to process all JSON files and create dataset."""
  start_time = datetime.now()

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

  # Find all JSON files
  json_files = find_json_files()

  if not json_files:
    print("No JSON files found in output/*/json/ directories")
    return

  print(f"Found {len(json_files)} JSON files to process")

  processed_files = []
  skipped_files = []
  processed_metadata_files = []

  for json_file in json_files:
    try:
      # Read JSON file
      with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

      # Check if question should be skipped
      if should_skip_question(json_data):
        skipped_files.append(json_file)
        print(f"Skipped: {json_file} (contains wrong answers)")
        continue

      # Post-process questions to fix wrong answers
      json_data = post_process_questions(json_data)

      # Get next file identifier
      file_id = get_next_file_id(data_dir)

      # Extract question data
      question_title, question_text, choices, question_type = extract_question_data(
        json_data)

      # Create TXT file content
      txt_content = create_txt_content(
        question_title, question_text, choices, question_type)

      # Write TXT file to data/ folder
      txt_filename = f"{file_id}.txt"
      txt_path = data_dir / txt_filename
      with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(txt_content)

      # Save post-processed JSON file to metadata/ folder
      json_filename = f"{file_id}.json"
      json_path = metadata_dir / json_filename
      with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

      # Look for and copy associated image
      image_file = find_associated_image(json_file, json_data)
      if image_file:
        # Get image extension
        image_path_obj = Path(image_file)
        ext = image_path_obj.suffix
        image_filename = f"{file_id}{ext}"
        image_dest_path = imgs_dir / image_filename
        shutil.copy2(image_file, image_dest_path)
        print(
          f"Processed: {json_file} -> {file_id}.txt, {file_id}.json, {file_id}{ext}")
      else:
        print(
          f"Processed: {json_file} -> {file_id}.txt, {file_id}.json (no image)")

      processed_files.append(json_file)
      processed_metadata_files.append(str(json_path))

    except Exception as e:
      print(f"Error processing {json_file}: {str(e)}")
      continue

  end_time = datetime.now()

  # Update metadata
  processing_metadata_file = metadata_dir / "processing_metadata.json"
  update_metadata(str(processing_metadata_file),
                  processed_files, start_time, end_time)

  # Collect statistics
  stats = collect_statistics_from_metadata(
    processed_metadata_files, str(imgs_dir))

  # Calculate version once for both files
  if version is None:
    if previous_version is not None:
      version = previous_version + REPORT_CONFIG['version_increment']
    else:
      version = REPORT_CONFIG['default_version']

  # Generate and write README.md
  report_content = generate_report(
    start_time, end_time, stats, dataset_dir, version)
  readme_file = dataset_path / REPORT_CONFIG['readme_filename']
  with open(readme_file, 'w', encoding='utf-8') as f:
    f.write(report_content)

  # Generate and write metadata.json
  metadata = generate_metadata(
    start_time, end_time, stats, dataset_dir, version)
  metadata_file = dataset_path / REPORT_CONFIG['metadata_filename']
  with open(metadata_file, 'w', encoding='utf-8') as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

  # Copy preprocessed images if requested
  if copy_preprocessed:
    print(f"\nCopying preprocessed images...")
    copy_preprocessed_images(dataset_dir, processed_metadata_files)

  print(f"\nProcessing complete!")
  print(f"Processed {len(processed_files)} files")
  print(f"Skipped {len(skipped_files)} files")
  print(f"Output directories:")
  print(f"  - Text files: {data_dir}")
  print(f"  - JSON metadata: {metadata_dir}")
  print(f"  - Images: {imgs_dir}")
  print(f"Duration: {(end_time - start_time).total_seconds():.2f} seconds")
  print(f"Reports generated:")
  print(f"  - README: {readme_file}")
  print(f"  - Metadata: {metadata_file}")


if __name__ == "__main__":
  main()
