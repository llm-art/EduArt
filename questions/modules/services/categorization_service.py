"""Question categorization service using LLM providers."""

import re
import json
import time
from datetime import datetime


# Categorization prompt template
CATEGORIZATION_PROMPT = """Classify the following art-history question along four axes.

AXES AND VALID VALUES:

1. art_historical: an ARRAY of one or more of "subject_matter_and_iconography", "object_and_work_type", "materials_and_techniques", "style_and_period", "authorship"
2. cultural_tradition: one of "western", "eastern", "middle_east"
3. disciplinary_domain: one of "art_history", "architectural_history"
4. epistemic_level: one of "factual_identification", "contextual_knowledge", "interpretive_reasoning"

QUESTION TITLE: {question_title}

QUESTION TEXT: {question_text}

CHOICES:
{choices_text}

Return ONLY a JSON object with the four keys above. No explanation, no markdown fences."""

# Valid category values for validation
VALID_CATEGORIES = {
    'art_historical': [
        'subject_matter_and_iconography',
        'object_and_work_type',
        'materials_and_techniques',
        'style_and_period',
        'authorship',
    ],
    'cultural_tradition': [
        'western',
        'eastern',
        'middle_east',
    ],
    'disciplinary_domain': [
        'art_history',
        'architectural_history',
    ],
    'epistemic_level': [
        'factual_identification',
        'contextual_knowledge',
        'interpretive_reasoning',
    ],
}


def categorize_question(provider, question_text, choices, question_title=""):
  """
  Classify a question along the four annotation axes using an LLM.

  Args:
      provider: LLM provider instance with a query() method
      question_text: The question text
      choices: List of formatted choice strings
      question_title: Optional question title for context

  Returns:
      Tuple of (categories_dict or None, ai_call_dict or None)
  """
  choices_text = "\n".join(choices) if choices else "(no choices)"
  prompt = CATEGORIZATION_PROMPT.format(
      question_title=question_title or "(none)",
      question_text=question_text,
      choices_text=choices_text,
  )

  start = time.time()
  try:
    response_text, token_metadata = provider.query(prompt)
  except Exception as e:
    print(f"    Warning: LLM categorization call failed: {e}")
    return None, None
  elapsed = time.time() - start

  # Build ai_call record
  provider_info = provider.get_provider_info()
  ai_call = {
      "description": "question categorization",
      "model_name": f"{provider_info.get('provider', 'unknown').title()} {provider_info.get('model', 'unknown')}",
      "input_tokens": token_metadata.get("input_tokens", 0),
      "output_tokens": token_metadata.get("output_tokens", 0),
      "total_tokens": token_metadata.get("input_tokens", 0) + token_metadata.get("output_tokens", 0),
      "processing_time": elapsed,
      "timestamp": datetime.now().isoformat(),
  }

  # Strip markdown fences if present
  text = response_text.strip()
  if text.startswith("```"):
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

  try:
    categories = json.loads(text)
  except json.JSONDecodeError:
    print(f"    Warning: Could not parse categorization JSON: {text[:120]}")
    return None, ai_call

  # Normalize art_historical to always be an array
  ah = categories.get('art_historical')
  if isinstance(ah, str):
    categories['art_historical'] = [ah]

  # Validate each axis
  for key, valid_values in VALID_CATEGORIES.items():
    value = categories.get(key)
    if key == 'art_historical':
      # art_historical must be a non-empty array with valid values
      if not isinstance(value, list) or len(value) == 0:
        print(f"    Warning: art_historical must be a non-empty array, got {value!r}")
        return None, ai_call
      for item in value:
        if item not in valid_values:
          print(f"    Warning: Invalid art_historical value {item!r}")
          return None, ai_call
    else:
      if value not in valid_values:
        print(f"    Warning: Invalid categorization value {key}={value!r}")
        return None, ai_call

  return categories, ai_call
