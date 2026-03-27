"""Dataset discovery and question data extraction utilities."""

import json
from pathlib import Path


def find_structured_folders():
  """Find all folders with a 'structured' subfolder in questions/."""
  structured_folders = []
  questions_dir = Path("questions")

  if not questions_dir.exists():
    print("Warning: 'questions' directory not found")
    return []

  # Look for all subdirectories in questions/ that contain a 'structured' folder
  for item in questions_dir.iterdir():
    if item.is_dir():
      structured_path = item / "structured"
      if structured_path.exists() and structured_path.is_dir():
        structured_folders.append(structured_path)

  return structured_folders


def find_json_files_in_structured(structured_path, question_types):
  """
  Find all JSON files in structured/{subfolder}/json/ directories.

  Args:
      structured_path: Path to the structured folder
      question_types: List of question types to filter by

  Returns:
      List of tuples: (json_file_path, source_folder_name, subfolder_name)
  """
  json_files = []

  # Get source name (e.g., "myzanichelli" or "ap_art_history")
  source_name = structured_path.parent.name

  # Iterate through all subfolders in structured/
  for subfolder in structured_path.iterdir():
    if not subfolder.is_dir():
      continue

    # Look for json/ directory inside each subfolder
    json_dir = subfolder / "json"
    if not json_dir.exists() or not json_dir.is_dir():
      continue

    # Find all JSON files in this json/ directory
    for json_file in json_dir.glob("*.json"):
      # Skip per-model extraction files (e.g. 1.google_gemini-2.5-pro.json)
      # Only process canonical ground truth files with numeric stems
      if not json_file.stem.isdigit():
        continue
      # Check if this JSON file contains questions of the desired type
      try:
        with open(json_file, 'r', encoding='utf-8') as f:
          data = json.load(f)

        # Handle both single question format and multiple questions format
        questions_to_check = []
        if "questions" in data and isinstance(data["questions"], list):
          # Multiple questions in one file
          questions_to_check = data["questions"]
        elif "type" in data:
          # Single question format
          questions_to_check = [data]

        # Check if any question matches the desired types
        for question in questions_to_check:
          if question.get("type") in question_types:
            json_files.append((json_file, source_name, subfolder.name))
            break  # Found at least one matching question, add file once

      except Exception as e:
        print(f"Warning: Could not read {json_file}: {e}")
        continue

  return json_files


def find_associated_image(json_file_path, image_ref, source_name, exercise_num, question_num):
  """
  Find associated image file for a question.

  Args:
      json_file_path: Path to the JSON file
      image_ref: Image reference from JSON (e.g., "imgs/2.jpg" or None)
      source_name: Source name (e.g., "myzanichelli" or "ap_art_history")
      exercise_num: Exercise number
      question_num: Question number

  Returns:
      Path to image file if found, None otherwise
  """
  # First, try using the image reference if provided
  if image_ref:
    # Get the parent directory of the json file (e.g., structured/2010/)
    json_parent = json_file_path.parent.parent

    # Construct the image path relative to the json parent
    image_path = json_parent / image_ref

    if image_path.exists():
      return image_path

  # For myzanichelli, try looking in the raw folder
  if source_name == "myzanichelli" and exercise_num is not None and question_num is not None:
    raw_image_path = Path(
      f"questions/myzanichelli/raw/{exercise_num}/imgs/{question_num}.jpg")
    if raw_image_path.exists():
      return raw_image_path

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


def process_true_false_answers(question_data):
    """
    Process true_false question answers:
    - Flip True/False when note is "Risposta sbagliata."
    - Remove note field from all answers

    Args:
        question_data: Question data dictionary

    Returns:
        Modified question_data with processed answers
    """
    if question_data.get("type") != "true_false":
        return question_data

    answers = question_data.get("answers", [])
    if not answers:
        return question_data

    processed_answers = []
    for answer in answers:
        processed_answer = answer.copy()

        # Check if we need to flip the answer
        if processed_answer.get("note") == "Risposta sbagliata.":
            text = processed_answer.get("text", "")
            if text == "True":
                processed_answer["text"] = "False"
            elif text == "False":
                processed_answer["text"] = "True"

        # Remove the note field
        if "note" in processed_answer:
            del processed_answer["note"]

        processed_answers.append(processed_answer)

    question_data["answers"] = processed_answers
    return question_data


def create_txt_content(question_title, question_text, choices, question_type=""):
  """Create the content for the TXT file."""
  content = []

  if question_text:
    content.append(question_text)
    content.append("")

  if choices:
    for choice in choices:
      content.append(choice)

  return "\n".join(content)
