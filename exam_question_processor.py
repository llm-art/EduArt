#!/usr/bin/env python3
"""
Enhanced LangChain + PaddleOCR + Multi-Model (Qwen2-VL/Gemini) pipeline for exam question processing

USAGE:
    python exam_question_processor.py

REQUIREMENTS:
    - paddleocr: Italian OCR text extraction
    - transformers: Qwen2-VL-Instruct local model (optional)
    - langchain-google-genai: Gemini 2.5 Pro API integration (optional)
    - langchain-core: Pipeline orchestration
    - pillow: Image handling
    - python-dotenv: Environment configuration

CONFIGURATION:
    Create a .env file based on .env.example to configure:
    - MODEL_TYPE: "qwen" (local) or "gemini" (API)
    - GOOGLE_API_KEY: Required for Gemini
    - Other model-specific settings

PIPELINE:
    Image → PaddleOCR → Vision Model (Qwen/Gemini) → Type Detection → Text Extraction → JSON

OUTPUT:
    Structured JSON with question data, confidence scoring, and SHA256 provenance
"""

import json
import hashlib
import re
from pathlib import Path
from typing import Dict, Any

import click
from paddleocr import PaddleOCR
from langchain_core.runnables import RunnableLambda
from PIL import Image

# Import our new model system
from models import create_vision_model
from config import Config


# Global model instances (loaded once)
ocr_model = None
vision_model = None


def load_prompts() -> tuple[str, str, str, str, str]:
  """Load prompts from external files"""
  base_dir = Path(__file__).parent
  dir_prompts = base_dir / "prompts"

  def read_prompt(file_path: Path) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
      return f.read().strip()

  # Load system prompt
  system_prompt = read_prompt(dir_prompts / "system_prompt.txt")
  extract_type = read_prompt(dir_prompts / "extract_type.txt")
  extract_text_multiple_choice = read_prompt(
      dir_prompts / "extract_text_multiple_choice.txt")
  extract_text_select_errors = read_prompt(
      dir_prompts / "extract_text_select_errors.txt")
  extract_text_positioning = read_prompt(
      dir_prompts / "extract_text_positioning.txt")
  extract_text_completion_open = read_prompt(
      dir_prompts / "extract_text_completion_open.txt")
  extract_text_completion_closed = read_prompt(
      dir_prompts / "extract_text_completion_closed.txt")
  extract_text_true_false = read_prompt(
      dir_prompts / "extract_text_true_false.txt")

  return system_prompt, extract_type, extract_text_multiple_choice, extract_text_select_errors, extract_text_positioning, extract_text_completion_open, extract_text_completion_closed, extract_text_true_false


# Load prompts from files
SYSTEM_PROMPT, EXTRACT_TYPE_PROMPT, EXTRACT_TEXT_PROMPT_MULTIPLE_CHOICE, EXTRACT_TEXT_PROMPT_SELECT_ERRORS, EXTRACT_TEXT_PROMPT_POSITIONING, EXTRACT_TEXT_PROMPT_COMPLETION_OPEN, EXTRACT_TEXT_PROMPT_COMPLETION_CLOSED, EXTRACT_TEXT_PROMPT_TRUE_FALSE = load_prompts()


def load_vision_model() -> None:
  """Load the configured vision model (Qwen or Gemini)"""
  global vision_model

  print(f"Loading vision model: {Config.MODEL_TYPE}")

  try:
    vision_model = create_vision_model()
    vision_model.load_model()

    model_info = vision_model.get_model_info()

  except Exception as e:
    print(f"Error loading vision model: {e}")
    raise


def load_ocr_model() -> None:
  """Load PaddleOCR model for Italian text recognition"""
  global ocr_model
  print("Loading PaddleOCR model...")

  ocr_model = PaddleOCR(
      lang=Config.OCR_LANG,
      text_detection_model_name=Config.TEXT_DETECTION_MODEL,
      text_recognition_model_name=Config.TEXT_RECOGNITION_MODEL,
      use_doc_orientation_classify=False,
      use_doc_unwarping=False,
      use_textline_orientation=False,
  )


def calculate_hash(image_path: str) -> str:
  """Calculate SHA256 hash of image file bytes"""
  with open(image_path, 'rb') as f:
    return hashlib.sha256(f.read()).hexdigest()


def vision_chat(image_path: str, system_prompt: str, user_prompt: str) -> str:
  """
  Call the configured vision model with image and text prompts

  Args:
      image_path: Path to the main image to analyze
      system_prompt: System prompt for the model
      user_prompt: User prompt with instructions

  Returns:
      Generated text response
  """
  global vision_model

  if not vision_model:
    load_vision_model()

  try:
    response = vision_model.chat(image_path, system_prompt, user_prompt)
    return response

  except Exception as e:
    print(f"Error in vision model chat: {e}")
    raise


def parse_json_with_fallback(text: str) -> Dict[str, Any]:
  """Parse JSON with fallback to substring extraction and completion"""

  if isinstance(text, list):
    text = text[0] if text else ""

  if not text or text.strip() == "":
    return {"type": "unknown"}

  # Remove Markdown code block if present using regex
  text = re.sub(r"^(?:```(?:json)?\s*)", "", text)
  text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)

  try:
    result = json.loads(text)
    return result
  except json.JSONDecodeError as e:
    print(f"Direct JSON parsing failed: {e}")
    return {"type": "unknown", "parsing_error": "failed_all_attempts"}


def read_html_file(file_path: Path) -> str:
  """Read HTML content from file"""
  with open(file_path, "r", encoding="utf-8") as f:
    return f.read()


def load_existing_ocr(data: Dict[str, Any]) -> str:
  """Load OCR text from existing JSON file if it exists"""
  ocr_path = data["output_path"] / f"{data['exercise']}/ocr/"
  ocr_file = ocr_path / f"{data['question']}.json"

  if ocr_file.exists():
    try:
      with open(ocr_file, 'r', encoding='utf-8') as f:
        ocr_data = json.load(f)

      # Extract text from OCR JSON structure
      ocr_text = ""
      if 'rec_texts' in ocr_data:
        ocr_text = " ".join(ocr_data['rec_texts']) + " "

      print(
        f"Loaded existing OCR from {ocr_file} (char length: {len(ocr_text)})")
      return ocr_text.strip()

    except Exception as e:
      print(f"Error loading existing OCR file {ocr_file}: {e}")
      return ""

  return ""


def ocr_step(data: Dict[str, Any]) -> Dict[str, Any]:
  """Extract text using PaddleOCR or load from existing files"""
  print(f"\nOCR step: question {data.get('question', 'unknown')}")

  if data is None:
    print("ERROR: data is None in ocr_step!")
    return {"error": "data_is_none_in_ocr"}

  # Check if we should use existing OCR files
  force_ocr = data.get('force_ocr', False)

  if not force_ocr:
    # Try to load existing OCR data
    existing_ocr_text = load_existing_ocr(data)
    if existing_ocr_text:
      print("Using existing OCR data")
      return {**data, "ocr_text": existing_ocr_text}

  print("Running OCR process...")

  try:
    # Run OCR
    global ocr_model

    if ocr_model is None:
      load_ocr_model()

    image_path = data["base_path"] / \
        f"{data['exercise']}/raw/{data['question']}.png"

    output = ocr_model.predict(input=str(image_path))

    # Save results
    ocr_path = data["output_path"] / f"{data['exercise']}/ocr/"
    ocr_path.mkdir(parents=True, exist_ok=True)

    # Concatenate all text
    ocr_text = ""
    for res in output:
      res.save_to_json(
          save_path=f"{ocr_path}/{Path(image_path).stem}.json")
      ocr_text += " ".join([txt for txt in res.str['res']['rec_texts']]) + " "

    print(f"OCR char length: {len(ocr_text)}")
    return {**data, "ocr_text": ocr_text.strip()}

  except Exception as e:
    print(f"OCR error: {e}")
    # Return original data with error flag and empty OCR text to prevent None propagation
    return {**data, "ocr_error": str(e), "ocr_text": ""}


def extract_question_type(data: Dict[str, Any]) -> Dict[str, Any]:
  """Extract complete question structure using unified prompt"""

  print(
    f"\nQuestion type extraction: question {data.get('question', 'unknown')}")

  html_text = read_html_file(
    data["base_path"] / f"{data['exercise']}/raw/{data['question']}.html")

  user_prompt = EXTRACT_TYPE_PROMPT.format(
      ocr_text=data["ocr_text"], html_text=html_text)

  image_path = data['base_path'] / \
      f"{data['exercise']}/raw/{data['question']}.png"

  try:
    response = vision_chat(str(image_path), SYSTEM_PROMPT, user_prompt)
    question_data = parse_json_with_fallback(response)

    print(f"Question type: {question_data.get('type', 'unknown')}")

    return {
        **data,
        **question_data,
    }

  except Exception as e:
    print(f"Question type extraction error: {e}")
    # Return original data with error flag to prevent None propagation
    return {**data, "extraction_error": str(e), "type": "unknown"}


def extract_question_text(data: Dict[str, Any]) -> Dict[str, Any]:
  """Extract question text only using the configured vision model"""

  print(
    f"\nQuestion text extraction: question {data.get('question', 'unknown')}")

  html_text = read_html_file(
    data["base_path"] / f"{data['exercise']}/raw/{data['question']}.html")

  image_path = data["base_path"] / \
      f"{data['exercise']}/raw/{data['question']}.png"

  if data["type"] == "multiple_choice":
    user_prompt = EXTRACT_TEXT_PROMPT_MULTIPLE_CHOICE.format(
        ocr_text=data["ocr_text"], html_text=html_text)

  elif data["type"] in ["select_errors", "highlight_errors"]:
    user_prompt = EXTRACT_TEXT_PROMPT_SELECT_ERRORS.format(
        ocr_text=data["ocr_text"], html_text=html_text)

  elif data["type"] == "positioning":
    # Use dedicated positioning prompt
    user_prompt = EXTRACT_TEXT_PROMPT_POSITIONING.format(
        ocr_text=data["ocr_text"], html_text=html_text)
  
  elif data["type"] == "completion_open":
    # Use dedicated completion open prompt
    user_prompt = EXTRACT_TEXT_PROMPT_COMPLETION_OPEN.format(
        ocr_text=data["ocr_text"], html_text=html_text)
  
  elif data["type"] == "completion_closed":
    # Use dedicated completion closed prompt
    user_prompt = EXTRACT_TEXT_PROMPT_COMPLETION_CLOSED.format(
        ocr_text=data["ocr_text"], html_text=html_text)
    
  elif data["type"] == "true_false":
    # Use dedicated true/false prompt
    user_prompt = EXTRACT_TEXT_PROMPT_TRUE_FALSE.format(
        ocr_text=data["ocr_text"], html_text=html_text)

  else:
    print(
      f"WARNING: Unknown question type '{data.get('type', 'None')}', using multiple choice prompt as fallback")
    user_prompt = EXTRACT_TEXT_PROMPT_MULTIPLE_CHOICE.format(
        ocr_text=data["ocr_text"], html_text=html_text)

  try:
    response = vision_chat(str(image_path), SYSTEM_PROMPT, user_prompt)
    question_data = parse_json_with_fallback(response)

    # Build result structure
    result = {
        **data,
        **question_data,
    }

    return result

  except Exception as e:
    print(f"Question text extraction error: {e}")
    # Return original data with error flag to prevent None propagation
    return {**data, "text_extraction_error": str(e)}


@click.command()
@click.option('--force-ocr', is_flag=True, help='Force OCR processing even if OCR JSON files already exist')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose/debug output')
@click.option('--exercise', '-e', default=1, help='Exercise number to process', show_default=True)
@click.option('--min-question', default=1, help='Minimum question number to process', show_default=True)
@click.option('--max-question', default=20, help='Maximum question number to process', show_default=True)
def main(force_ocr, verbose, exercise, min_question, max_question):
  """Process multiple questions using LangChain sequential batch processing with multi-model support"""

  print("=== Enhanced Multi-Model Exam Question Processor ===")
  print(f"Configuration: {Config.get_model_info()}")
  print(f"Force OCR: {force_ocr}")
  print(f"Verbose: {verbose}")
  print(f"Exercise: {exercise}")
  print(f"Questions: {min_question}-{max_question}")

  # Set global verbose flag for models
  Config.VERBOSE = verbose

  # Load models once
  load_vision_model()

  # Create unified LangChain pipeline
  ocr_runnable = RunnableLambda(ocr_step)
  extract_type_runnable = RunnableLambda(extract_question_type)
  extract_text_runnable = RunnableLambda(extract_question_text)

  # Chain them together - this creates a RunnableSequence
  pipeline = ocr_runnable | extract_type_runnable | extract_text_runnable

  # Batch processing parameters
  BASE_DIR = Path(__file__).parent
  base_path = BASE_DIR / "questions/data/"
  output_path = BASE_DIR / f"questions/output/"

  # Prepare batch input data
  batch_inputs = [
      {
          "base_path": base_path,
          "output_path": output_path,
          "exercise": exercise,
          "question": question,
          "force_ocr": force_ocr
      }
      for question in range(min_question, max_question + 1)
  ]

  print(
    f"Starting LangChain sequential batch processing of exercise {exercise}, questions {min_question}-{max_question}...")
  print(f"Using {Config.MODEL_TYPE.upper()} model")

  try:
    # Use LangChain's batch method for sequential processing
    # This processes inputs one by one in sequence
    results = pipeline.batch(
        batch_inputs,
        config={
            "max_concurrency": 1,  # Ensures sequential processing
            "return_exceptions": True  # Continue processing even if some fail
        }
    )

    # Process and save results
    successful_count = 0
    failed_count = 0

    for i, result in enumerate(results):
      question = min_question + i

      if isinstance(result, Exception):
        print(f"Error processing question {question}: {result}")
        failed_count += 1
        continue

      try:
        # Add image path if applicable
        result.setdefault("image", str(
          base_path / f"{exercise}/imgs/{question}.jpg") if "has_image" in result else None)

        # Save individual result
        parsed_path = output_path / f"{exercise}/json/{question}.json"
        parsed_path.parent.mkdir(parents=True, exist_ok=True)

        result["base_path"] = str(base_path)
        result["output_path"] = str(output_path)

        with open(parsed_path, "w", encoding="utf-8") as f:
          json.dump(result, f, indent=2, ensure_ascii=False)

        successful_count += 1
        question_type = result.get("type", "unknown")
        print(
          f"Successfully processed question {question} (type: {question_type})")

      except Exception as e:
        print(f"Error saving question {question}: {e}")
        failed_count += 1

    # Print batch summary
    print(f"\n=== Multi-Model Processing Summary ===")
    print(f"Model: {Config.MODEL_TYPE.upper()}")
    print(f"Exercise: {exercise}")
    print(f"Total questions: {max_question - min_question + 1}")
    print(f"Successful: {successful_count}")
    print(f"Failed: {failed_count}")
    print(f"Results saved to: {output_path}/{exercise}/json/")

    return [r for r in results if not isinstance(r, Exception)]

  except Exception as e:
    print(f"Batch processing error: {e}")
    return []


def any_ocr_files_missing(exercise: int, min_question: int, max_question: int) -> bool:
  """Check if any OCR files are missing for the given range"""
  BASE_DIR = Path(__file__).parent
  output_path = BASE_DIR / f"questions/output/"
  ocr_path = output_path / f"{exercise}/ocr/"

  for question in range(min_question, max_question + 1):
    ocr_file = ocr_path / f"{question}.json"
    if not ocr_file.exists():
      return True

  return False


if __name__ == "__main__":
  main()
