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
    Image → PaddleOCR → Qwen2-VL Classification → Qwen2-VL Extraction → JSON

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

# Italian prompts
SYSTEM_PROMPT = "Sei un estrattore meticoloso di domande di Storia dell'Arte. Ricevi uno screenshot e il relativo testo OCR. Devi restituire SOLO JSON valido secondo lo schema richiesto. Non aggiungere commenti. Non inventare. Se mancano dati, usa null e abbassa confidence."

CLASSIFY_PROMPT = "Classifica il tipo di domanda tra: multiple_choice_single, true_false, fill_in_blank, matching, short_answer, open_ended, image_reference. Rispondi SOLO con JSON {{\"type\":\"...\",\"confidence\":0.0}}. Testo OCR (rumoroso):\n{ocr_text}\n"

EXTRACT_PROMPT = "Estrai la domanda in testo in SOLO JSON (nessun commento) con lo schema FINAL OUTPUT. Vincoli: non creare opzioni che non compaiono nello screenshot; se la soluzione non è esplicita, 'answer': null e confidence più bassa. Usa 'language': 'it', metti l'immagine in 'images'. Testo OCR (rumoroso):\n{ocr_text}\n"


def calculate_hash(image_path: str) -> str:
  """Calculate SHA256 hash of image file bytes"""
  with open(image_path, 'rb') as f:
    return hashlib.sha256(f.read()).hexdigest()


def ocr_step(data: Dict[str, Any]) -> Dict[str, Any]:
  """Extract text using PaddleOCR"""
  global ocr_model

  print("Loading PaddleOCR")
  ocr_model = PaddleOCR(lang="it",
                        text_detection_model_name="PP-OCRv5_mobile_det",
                        text_recognition_model_name="PP-OCRv5_mobile_rec",
                        use_doc_orientation_classify=False,
                        use_doc_unwarping=False,
                        use_textline_orientation=False,
                        )

  # Run OCR
  output = ocr_model.predict(input=str(data["image_path"]))

  # Save results
  output_path = data["output_path"]
  output_path.mkdir(parents=True, exist_ok=True)

  # Concatenate all text
  ocr_text = ""
  for res in output:
    res.print()
    res.save_to_img(save_path=f"{output_path}/1.png")
    res.save_to_json(save_path=f"{output_path}/1.json")
    ocr_text += " ".join([txt for txt in res.str['res']['rec_texts']]) + " "

  return {
      "image_path": data["image_path"],
      "ocr_text": ocr_text.strip(),
      "hash": calculate_hash(data["image_path"])
  }


def qwen_chat(image_path: str, system_prompt: str, user_prompt: str) -> str:
  """Call Qwen2-VL with image and text"""
  
  print("Loading Qwen2-VL model...")
  model_name = "Qwen/Qwen2-VL-2B-Instruct"
  qwen_model = Qwen2VLForConditionalGeneration.from_pretrained(
      model_name,
      dtype="auto",
      #attn_implementation="flash_attention_2",
      device_map="auto"
  )
  qwen_processor = AutoProcessor.from_pretrained(model_name)

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
              {"type": "image", "image": image, "resized_height": 280, "resized_width": 420},
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


def classify_step(data: Dict[str, Any]) -> Dict[str, Any]:
  """Classify question type using Qwen2-VL"""
  user_prompt = CLASSIFY_PROMPT.format(ocr_text=data["ocr_text"])

  try:
    response = qwen_chat(data["image_path"], SYSTEM_PROMPT, user_prompt)
    classification = parse_json_with_fallback(response)

    data["question_type"] = classification.get("type", "unknown")
    data["type_confidence"] = classification.get("confidence", 0.5)

  except Exception as e:
    print(f"Classification error: {e}")
    data["question_type"] = "unknown"
    data["type_confidence"] = 0.1

  return data


def extract_step(data: Dict[str, Any]) -> Dict[str, Any]:
  """Extract structured question data using Qwen2-VL"""
  user_prompt = EXTRACT_PROMPT.format(ocr_text=data["ocr_text"])

  try:
    response = qwen_chat(data["image_path"], SYSTEM_PROMPT, user_prompt)
    extracted = parse_json_with_fallback(response)

    # Build final JSON structure
    result = {
        "id": Path(data["image_path"]).stem,
        "type": data["question_type"],
        "language": "it",
        "stem": extracted.get("stem", ""),
        "choices": extracted.get("choices", []),
        "answer": extracted.get("answer"),
        "explanations": None,
        "artwork_refs": [],
        "images": [{"path": data["image_path"], "caption": None}],
        "confidence": min(data["type_confidence"], extracted.get("confidence", 0.5)),
        "provenance": {"hash": data["hash"]}
    }

    # Adjust confidence if answer is missing for MCQ
    if result["type"] == "multiple_choice_single" and not result["answer"]:
      result["confidence"] *= 0.7

  except Exception as e:
    print(f"Extraction error: {e}")
    # Minimal fallback structure
    result = {
        "id": Path(data["image_path"]).stem,
        "type": data["question_type"],
        "language": "it",
        "stem": data["ocr_text"][:200] + "..." if len(data["ocr_text"]) > 200 else data["ocr_text"],
        "choices": [],
        "answer": None,
        "explanations": None,
        "artwork_refs": [],
        "images": [{"path": data["image_path"], "caption": None}],
        "confidence": 0.2,
        "provenance": {"hash": data["hash"]}
    }

  return result


def main():
  """Main processing pipeline"""
  # Create LangChain pipeline
  ocr_runnable = RunnableLambda(ocr_step)
  classify_runnable = RunnableLambda(classify_step)
  extract_runnable = RunnableLambda(extract_step)

  # Chain them together
  pipeline = ocr_runnable | classify_runnable | extract_runnable

  exercise = 1
  question = 1

  # Test with sample image
  BASE_DIR = Path(__file__).parent
  output_path = BASE_DIR / f"questions/data/{exercise}/ocr/"
  sample_image = BASE_DIR / f"questions/data/{exercise}/raw/{question}.png"

  data = {
    "image_path": sample_image,
    "output_path": output_path
  }

  if not Path(sample_image).exists():
    print(f"Sample image not found: {sample_image}")
    print("Please provide a valid image path")
    return

  print(f"Processing: {sample_image}")

  try:
    # Run the pipeline
    result = pipeline.invoke(data)

    # Print final JSON
    print("\nFinal JSON:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

  except Exception as e:
    print(f"Pipeline error: {e}")


if __name__ == "__main__":
  main()
