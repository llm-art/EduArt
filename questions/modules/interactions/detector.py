"""
Question type detection module.

This module analyzes HTML content and text to determine the type of question
being displayed, enabling appropriate interaction strategies.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from playwright.async_api import Page


class QuestionTypeDetector:
  """Detects question types based on HTML structure and content."""

  # Question type patterns for detection
  QUESTION_TYPE_PATTERNS = {
    'multiple_choice_radio': {
        'html_indicators': [
            'input[type="radio"]',
        ],
        'selectors': [
            'input[type="radio"]',
        ],
    },
      'scelta_multipla': {
          'html_indicators': [
              'input[type="radio"]',
              'input[type="checkbox"]',
          ],
          'selectors': [
              'input[type="radio"]',
              'input[type="checkbox"]',
          ],
      },
      'completamento_chiuso': {
          'html_indicators': [
              'choiceChip',
              'sc-bmCFzp',
              'sc-lcsTPt',
              'sc-gZEilz',
              'role="button"',
              'tabindex="0"'
          ],
          'text_indicators': [
              'scegliendo',
              'termini corretti',
              'Ricostruisci',
              'periodo',
              'completa'
          ],
          'selectors': [
              '.choiceChip',
              '.sc-bmCFzp',
              '.sc-lcsTPt[role="button"]',
              'span[role="button"][tabindex="0"]'
          ],
          'weight': 8
      },
      'vero_falso': {
          'html_indicators': [
              'value="true"',
              'value="false"',
              'assertion-',
              'name="assertion'
          ],
          'text_indicators': [
              'Vero',
              'Falso',
              'vere e quelle false',
              'affermazioni vere',
              'Individua le affermazioni'
          ],
          'selectors': [
              'input[value="true"]',
              'input[value="false"]',
              'input[name*="assertion"]'
          ],
          'weight': 9
      },
      'positioning': {
          'html_indicators': [
              'draggable="true"',
              'sc-fneYkE',
              'sc-klOCnl',
              'sc-dPhEwk',
              'sc-bvouTE'
          ],
          'text_indicators': [
              'trascina',
              'posiziona',
              'Come si fa?',
              'clicca, tieni premuto',
              'trascinala'
          ],
          'selectors': [
              '[draggable="true"]',
              '.sc-fneYkE',
              '.sc-klOCnl',
              '.sc-dPhEwk'
          ],
          'weight': 7
      },
      'trova_errore': {
          'html_indicators': [
              'ERRORI EVIDENZIATI',
              'evidenziati',
              'errori'
          ],
          'text_indicators': [
              'errori',
              'evidenziati',
              'selezione',
              'parti di testo',
              'sbagliate'
          ],
          'selectors': [
              '[class*="error"]',
              '[class*="highlight"]',
              '[class*="evidenziati"]'
          ],
          'weight': 6
      },
      'completamento_aperto': {
          'html_indicators': [
              'input',
              'text',
              'textarea',
              'contenteditable'
          ],
          'text_indicators': [
              'completa',
              'inserendo',
              'termini',
              'descrizione',
              'Per inserire'
          ],
          'selectors': [
              'input[type="text"]',
              'textarea',
              '[contenteditable="true"]'
          ],
          'weight': 5
      }
  }

  def __init__(self, page: Page):
    """
    Initialize the question type detector.

    Args:
        page: Playwright page instance
    """
    self.page = page

  async def detect_question_type(self, content: Dict[str, Any]) -> Tuple[str, float]:
    """
    Detect the type of question based on content.

    Args:
        content: Dictionary containing 'html' and 'text' keys

    Returns:
        Tuple of (question_type, confidence_score)
    """
    html_content = content.get('html', '').lower()
    text_content = content.get('text', '').lower()

    print("Analyzing question content for type detection...")

    question_type = 'unknown'

    # Score each question type
    type_scores = {}

    for question_type, patterns in self.QUESTION_TYPE_PATTERNS.items():
      score = await self._calculate_type_score(
          question_type,
          patterns,
          html_content,
          text_content
      )
      type_scores[question_type] = score
      print(f"  {question_type}: {score:.2f}")

    # Find the highest scoring type
    if not type_scores:
      return 'unknown', 0.0

    best_type = max(type_scores, key=type_scores.get)
    best_score = type_scores[best_type]

    # Require minimum confidence threshold
    min_confidence = 0.3
    if best_score < min_confidence:
      print(
        f"Low confidence ({best_score:.2f}) for type detection, marking as unknown")
      return 'unknown', best_score

    print(
      f"Detected question type: {best_type} (confidence: {best_score:.2f})")
    return best_type, best_score

  async def _calculate_type_score(
      self,
      question_type: str,
      patterns: Dict[str, Any],
      html_content: str,
      text_content: str
  ) -> float:
    """
    Calculate confidence score for a specific question type.

    Args:
        question_type: Type of question being scored
        patterns: Pattern dictionary for this question type
        html_content: HTML content (lowercase)
        text_content: Text content (lowercase)

    Returns:
        Confidence score (0.0 to 1.0)
    """
    score = 0.0
    max_score = 0.0

    # Check HTML indicators
    html_indicators = patterns.get('html_indicators', [])
    for indicator in html_indicators:
      max_score += 1
      if indicator.lower() in html_content:
        score += 1

    # Check text indicators
    """
        text_indicators = patterns.get('text_indicators', [])
        for indicator in text_indicators:
            max_score += 1
            if indicator.lower() in text_content:
                score += 1
        """

    # Check if selectors exist on page (higher weight)
    selectors = patterns.get('selectors', [])
    for selector in selectors:
      max_score += 2  # Higher weight for actual DOM elements
      try:
        elements = await self.page.query_selector_all(selector)
        if elements:
          score += 2
          break  # Only count once per type
      except Exception as e:
        print(f"Error checking selector {selector}: {e}")
        continue

    # Apply type-specific weight
    weight = patterns.get('weight', 1)
    weighted_score = (score / max_score if max_score >
                      0 else 0) * (weight / 10)

    return min(weighted_score, 1.0)  # Cap at 1.0

  async def get_interaction_elements(self, question_type: str) -> List[Any]:
    """
    Get DOM elements that can be interacted with for the given question type.

    Args:
        question_type: Detected question type

    Returns:
        List of DOM elements for interaction
    """
    if question_type not in self.QUESTION_TYPE_PATTERNS:
      return []

    patterns = self.QUESTION_TYPE_PATTERNS[question_type]
    selectors = patterns.get('selectors', [])

    elements = []
    for selector in selectors:
      try:
        found_elements = await self.page.query_selector_all(selector)
        elements.extend(found_elements)
      except Exception as e:
        print(f"Error finding elements with selector {selector}: {e}")
        continue

    print(f"Found {len(elements)} interaction elements for {question_type}")
    return elements

  def get_question_type_info(self, question_type: str) -> Dict[str, Any]:
    """
    Get information about a specific question type.

    Args:
        question_type: Question type to get info for

    Returns:
        Dictionary with question type information
    """
    if question_type not in self.QUESTION_TYPE_PATTERNS:
      return {
          'type': question_type,
          'description': 'Unknown question type',
          'interaction_strategy': 'skip',
          'selectors': []
      }

    patterns = self.QUESTION_TYPE_PATTERNS[question_type]

    descriptions = {
        'scelta_multipla': 'Multiple choice question with radio buttons',
        'completamento_chiuso': 'Closed completion with clickable chips/buttons',
        'vero_falso': 'True/False question with multiple statements',
        'positioning': 'Drag and drop positioning question',
        'trova_errore': 'Find errors in text (skip interaction)',
        'completamento_aperto': 'Open completion with text input fields'
    }

    return {
        'type': question_type,
        'description': descriptions.get(question_type, 'Unknown question type'),
        'selectors': patterns.get('selectors', []),
        'weight': patterns.get('weight', 1)
    }
