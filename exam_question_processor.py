#!/usr/bin/env python3
"""
Minimal LangChain + PaddleOCR + Qwen2-VL pipeline for exam question processing

USAGE:
    python exam_question_processor.py

REQUIREMENTS:
    - paddleocr: Italian OCR text extraction
    - transformers: Qwen2-VL-Instruct local model
    - langchain-core: Pipeline orchestration
    - pillow: Image handling
    - torch, torchvision, accelerate: ML dependencies

PIPELINE:
    Image → PaddleOCR → Qwen2-VL Unified Extraction → JSON

OUTPUT:
    Structured JSON with question data, confidence scoring, and SHA256 provenance
"""

import json
import hashlib
import re
from pathlib import Path
from typing import Dict, Any

from paddleocr import PaddleOCR, TextRecognition, TextDetection
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from langchain_core.runnables import RunnableLambda
from PIL import Image
import torch


# Global model instances (loaded once)
ocr_model = None
qwen_model = None
qwen_processor = None


def load_prompts() -> tuple[str, str]:
  """Load prompts from external files"""
  base_dir = Path(__file__).parent

  dir_prompts = base_dir / "prompts"

  def read_prompt(file_path: Path) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
      return f.read().strip()

  # Load system prompt
  system_prompt = read_prompt(dir_prompts / "system_prompt.txt")
  extract_type = read_prompt(dir_prompts / "extract_type.txt")
  extract_text = read_prompt(dir_prompts / "extract_text_multiple_choice.txt")

  return system_prompt, extract_type, extract_text


# Load prompts from files
SYSTEM_PROMPT, EXTRACT_TYPE_PROMPT, EXTRACT_TEXT_PROMPT_MULTIPLE_CHOICE = load_prompts()


def load_qwen_model(model_name: str = "Qwen/Qwen2-VL-2B-Instruct") -> None:
  """Load Qwen2-VL model and processor.

  Args:
      model_name (str, optional): Model name to load. Defaults to "Qwen/Qwen2-VL-2B-Instruct".
  """
  global qwen_model, qwen_processor
  print("Loading Qwen2-VL model...")
  model_name = model_name
  qwen_model = Qwen2VLForConditionalGeneration.from_pretrained(
      model_name,
      dtype="auto",
      device_map="auto"
      # attn_implementation="flash_attention_2",
  )

  qwen_processor = AutoProcessor.from_pretrained(model_name)


def load_ocr_model(text_detection_model_name: str = "PP-OCRv5_mobile_det", text_recognition_model_name: str = "PP-OCRv5_mobile_rec") -> None:
  """Load PaddleOCR model for Italian text recognition.

  Args:
      text_detection_model_name (str, optional): Model name for text detection. Defaults to "PP-OCRv5_mobile_det".
      text_recognition_model_name (str, optional): Model name for text recognition. Defaults to "PP-OCRv5_mobile_rec".
  """
  global ocr_model
  print("Loading PaddleOCR model...")
  ocr_model = PaddleOCR(lang="it",
                        text_detection_model_name=text_detection_model_name,
                        text_recognition_model_name=text_recognition_model_name,
                        use_doc_orientation_classify=False,
                        use_doc_unwarping=False,
                        use_textline_orientation=False,
                        )


def calculate_hash(image_path: str) -> str:
  """Calculate SHA256 hash of image file bytes"""
  with open(image_path, 'rb') as f:
    return hashlib.sha256(f.read()).hexdigest()


def qwen_chat(image_path: str, system_prompt: str, user_prompt: str) -> str:
  """Call Qwen2-VL with image and text"""

  global qwen_model, qwen_processor

  # Load image
  image = Image.open(image_path)

  # Prepare messages
  messages = [
      {
          "role": "system",
          "content": system_prompt
      },
      {
          "role": "user",
          "content": [
              {"type": "image", "image": image,
               "resized_height": 720, "resized_width": 1280},
              {"type": "text", "text": user_prompt}
          ]
      }
  ]

  # Process with Qwen
  text = qwen_processor.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True)
  inputs = qwen_processor(
    text=[text], images=[image], padding=True, return_tensors="pt")
  inputs = inputs.to(qwen_model.device)

  # Generate response
  with torch.no_grad():
    generated_ids = qwen_model.generate(
      **inputs, max_new_tokens=512, do_sample=False)
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = qwen_processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]

  return output_text.strip()


def parse_json_with_fallback(text: str) -> Dict[str, Any]:
  """Parse JSON with fallback to substring extraction"""
  try:
    return json.loads(text)
  except json.JSONDecodeError:
    # Try to extract JSON from {...} substring
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
      try:
        return json.loads(match.group())
      except json.JSONDecodeError:
        pass

    # Return minimal fallback
    return {"type": "unknown", "confidence": 0.1}


def read_html_file(file_path: Path) -> str:
  """Read HTML content from file"""
  with open(file_path, "r", encoding="utf-8") as f:
    return f.read()

def ocr_step(data: Dict[str, Any]) -> Dict[str, Any]:
  """Extract text using PaddleOCR"""

  # Run OCR
  global ocr_model

  image_path = data["base_path"] / f"{data['exercise']}/raw/{data['question']}.png"


  output = ocr_model.predict(input=str(image_path))

  # Save results
  ocr_path = data["base_path"] / f"{data['exercise']}/ocr/"
  ocr_path.mkdir(parents=True, exist_ok=True)

  # Concatenate all text
  ocr_text = ""
  for res in output:
    res.save_to_json(
      save_path=f"{ocr_path}/{Path(image_path).stem}.json")
    ocr_text += " ".join([txt for txt in res.str['res']['rec_texts']]) + " "

  return {**data, "ocr_text": ocr_text.strip()}


def extract_question_type(data: Dict[str, Any]) -> Dict[str, Any]:
  """Extract complete question structure using unified prompt"""

  user_prompt = EXTRACT_TYPE_PROMPT.format(
    ocr_text=data["ocr_text"])

  image_path = data['base_path'] / f"{data['exercise']}/raw/{data['question']}.png"

  try:
    response = qwen_chat(str(image_path), SYSTEM_PROMPT, user_prompt)
    question_data = parse_json_with_fallback(response)

    return {
      **data,
      **question_data,
    }

  except Exception as e:
    print(f"Question extraction error: {e}")


def extract_question_text(data: Dict[str, Any]) -> Dict[str, Any]:
  """Extract question text only using Qwen2-VL"""

  html_text = read_html_file(data["base_path"] / f"{data['exercise']}/raw/{data['question']}.html")
  image_path = data['base_path'] / f"{data['exercise']}/raw/{data['question']}.png"

  if data["type"] == "multiple_choice":
    user_prompt = EXTRACT_TEXT_PROMPT_MULTIPLE_CHOICE.format(
        ocr_text=data["ocr_text"], html_text=html_text)

  try:
    response = qwen_chat(image_path, SYSTEM_PROMPT, user_prompt)
    question_data = parse_json_with_fallback(response)

    # Build result structure
    result = {
        **data,
        **question_data,
    }

    return result

  except Exception as e:
    print(f"Question text extraction error: {e}")


def main():
  """Unified processing pipeline with single-pass extraction"""

  # Ensure models are loaded
  load_qwen_model()
  load_ocr_model()

  # Create unified LangChain pipeline
  ocr_runnable = RunnableLambda(ocr_step)
  extract_type_runnable = RunnableLambda(extract_question_type)
  extract_text_runnable = RunnableLambda(extract_question_text)

  # Chain them together - single pass extraction
  pipeline = ocr_runnable | extract_type_runnable | extract_text_runnable

  exercise = 1
  question = 2

  # Test with sample image
  BASE_DIR = Path(__file__).parent
  base_path = BASE_DIR / f"questions/data/"

  data = {
    "base_path": base_path,
    "exercise": exercise,
    "question": question
  }

  try:
    # Run the pipeline
    result = pipeline.invoke(data)

    # add image
    result.setdefault("image", str(base_path / f"{exercise}/imgs/{question}.jpg") if "has_image" in result else None)

    # Print final JSON
    parsed_path = base_path / f"{exercise}/parsed/{question}.json"
    parsed_path.parent.mkdir(parents=True, exist_ok=True)

    result["base_path"] = str(base_path)

    with open(parsed_path, "w", encoding="utf-8") as f:
      json.dump(result, f, indent=2, ensure_ascii=False)

  except Exception as e:
    print(f"Pipeline error: {e}")


if __name__ == "__main__":
  main()
