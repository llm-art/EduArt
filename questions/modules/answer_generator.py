#!/usr/bin/env python3
"""
Question answering component using configurable LLM with image support.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from .models import create_vision_model
from .config import Config


class QuestionAnswerer:
  def __init__(self):
    self.vision_model = None
    self.prompt_template = self._load_prompt_template()

  def _load_prompt_template(self) -> str:
    """Load the universal prompt template."""
    prompt_path = Path(__file__).parent.parent.parent / "prompts" / "answer_question.txt"
    with open(prompt_path, 'r', encoding='utf-8') as f:
      return f.read().strip()

  def load_model(self):
    """Load the configured vision model."""
    if not self.vision_model:
      print(f"Loading vision model: {Config.MODEL_TYPE}")
      self.vision_model = create_vision_model()
      self.vision_model.load_model()
      print("✅ Vision model loaded successfully")

  def answer_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate an answer for a question using LLM.

    Args:
        question_data: Question data from JSON file

    Returns:
        Dictionary with generated answer and metadata
    """
    if not self.vision_model:
      self.load_model()

    # Format the prompt
    prompt = self._format_prompt(question_data)

    # Get image path if available
    image_path = question_data.get('image')
    if image_path and not Path(image_path).exists():
      print(f"⚠️ Warning: Image file not found: {image_path}")
      image_path = None

    try:
      print(
        f"Generating answer for question {question_data.get('question', '?')}...")
      print(f"Question type: {question_data.get('type', 'unknown')}")
      print(f"Using image: {'Yes' if image_path else 'No'}")

      # Generate answer using vision model
      response = self.vision_model.chat(
          image_path=image_path,
          system_prompt="You are an expert Art History student.",
          user_prompt=prompt
      )

      # Clean and format the response
      answer = self._clean_response(response, question_data.get('type'))

      print(f"Raw LLM response: {response}")
      print(f"Cleaned answer: {answer}")

      return {
          'success': True,
          'generated_answer': answer,
          'raw_response': response,
          'model_used': Config.MODEL_TYPE,
          'used_image': image_path is not None
      }

    except Exception as e:
      print(f"❌ Error generating answer: {e}")
      return {
          'success': False,
          'error': str(e),
          'generated_answer': None
      }

  def _format_prompt(self, question_data: Dict[str, Any]) -> str:
    """Format the universal prompt with question data."""
    choices_text = ""
    if question_data.get('choices'):
      choices_text = "OPTIONS:\n"
      for choice in question_data['choices']:
        choices_text += f"{choice['id']}. {choice['text']}\n"

    return self.prompt_template.format(
        question_type=question_data.get('type', 'unknown'),
        question_title=question_data.get('question_title', ''),
        question_text=question_data.get('question_text', ''),
        language=question_data.get('language', 'it'),
        choices_text=choices_text
    )

  def _clean_response(self, response: str, question_type: str) -> str:
    """Clean and format the LLM response based on question type."""
    response = response.strip()

    if question_type in ['multiple_choice', 'true_false']:
      # Extract just the letter for multiple choice/true-false
      import re
      letter_match = re.search(r'\b([A-E])\b', response)
      if letter_match:
        return letter_match.group(1)

      # Fallback: look for the first letter in the response
      first_letter = re.search(r'([A-E])', response)
      if first_letter:
        return first_letter.group(1)

    return response


if __name__ == "__main__":
  # Simple test
  answerer = QuestionAnswerer()

  # Test with a sample question data
  test_question = {
      "type": "multiple_choice",
      "question_title": "Test Question",
      "question_text": "What is the capital of Italy?",
      "choices": [
          {"id": "A", "text": "Rome"},
          {"id": "B", "text": "Milan"},
          {"id": "C", "text": "Naples"}
      ],
      "language": "it"
  }

  result = answerer.answer_question(test_question)
  print(f"Test result: {result}")
