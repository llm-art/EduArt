"""
Question interaction handler.

This module coordinates question type detection and interaction strategies,
including the "CORREGGI ESERCIZIO" button functionality.
"""

import asyncio
import random
from ..browser.selectors import SelectorStrategies
from typing import Dict, Any, Optional, Tuple
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .detector import QuestionTypeDetector
from .strategies import (
    SceltaMultiplaStrategy,
    CompletamentoChiusoStrategy,
    VeroFalsoStrategy,
    PositioningStrategy,
    TrovaErroreStrategy,
    CompletamentoApertoStrategy
)


class QuestionInteractionHandler:
  """Handles question interaction workflow including type detection and interaction."""

  def __init__(self, page: Page):
    """
    Initialize the question interaction handler.

    Args:
        page: Playwright page instance
    """
    self.page = page
    self.detector = QuestionTypeDetector(page)

    # Initialize interaction strategies
    self.strategies = {
        'scelta_multipla': SceltaMultiplaStrategy(page),
        'completamento_chiuso': CompletamentoChiusoStrategy(page),
        'vero_falso': VeroFalsoStrategy(page),
        'positioning': PositioningStrategy(page),
        'trova_errore': TrovaErroreStrategy(page),
        'completamento_aperto': CompletamentoApertoStrategy(page)
    }

    # Selectors for "CORREGGI ESERCIZIO" button
    self.correggi_selectors = [
        'button:has-text("CORREGGI ESERCIZIO")',
        'button:has-text("Correggi esercizio")',
        'button:has-text("correggi esercizio")',
        'button:has-text("CORREGGI")',
        'button:has-text("Correggi")',
        '[data-testid*="correct"]',
        '[data-testid*="check"]',
        'button[class*="correct"]',
        'button[class*="check"]',
        '.sc-button:has-text("CORREGGI")',
        'z-button:has-text("CORREGGI")'
    ]

  async def process_question_interaction(self, content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Complete question interaction workflow.

    This method:
    1. Detects question type
    2. Performs randomized interaction
    3. Clicks "CORREGGI ESERCIZIO" button
    4. Waits for results to load

    Args:
        content: Question content dictionary with 'html' and 'text'

    Returns:
        Dictionary with interaction results
    """
    results = {
        'success': False,
        'question_type': 'unknown',
        'confidence': 0.0,
        'interaction_performed': False,
        'correggi_clicked': False,
        'errors': []
    }

    try:
      print("=" * 60)
      print("STARTING QUESTION INTERACTION WORKFLOW")
      print("=" * 60)

      # Try to interact with the answers.

      await self._perform_question_interaction()

      """
            # Step 1: Detect question type
            question_type, confidence = await self.detector.detect_question_type(content)
            results['question_type'] = question_type
            results['confidence'] = confidence
            
            if question_type == 'unknown':
                print("⚠️ Unknown question type detected, skipping interaction")
                results['errors'].append('Unknown question type detected')
                # Still try to click CORREGGI ESERCIZIO even if type is unknown
            else:
                print(f"📋 Detected question type: {question_type} (confidence: {confidence:.2f})")
                
                # Step 2: Perform interaction based on type
                interaction_success = await self._perform_question_interaction(question_type)
                results['interaction_performed'] = interaction_success
                
                if not interaction_success:
                    results['errors'].append(f'Failed to interact with {question_type} question')
            """

      # Step 3: Click "CORREGGI ESERCIZIO" button
      correggi_success = await self._click_correggi_esercizio()
      results['correggi_clicked'] = correggi_success

      if not correggi_success:
        results['errors'].append('Failed to click CORREGGI ESERCIZIO button')

      # Step 4: Wait for results to load
      if correggi_success:
        await self._wait_for_results()
        print("✅ Question interaction workflow completed successfully")
        results['success'] = True
      else:
        print("⚠️ Question interaction completed with warnings")
        results['success'] = len(results['errors']) == 0

    except Exception as e:
      error_msg = f"Error in question interaction workflow: {e}"
      print(f"❌ {error_msg}")
      results['errors'].append(error_msg)

    print("=" * 60)
    print("QUESTION INTERACTION WORKFLOW SUMMARY")
    print("=" * 60)
    print(f"Question Type: {results['question_type']}")
    print(f"Confidence: {results['confidence']:.2f}")
    print(f"Interaction Performed: {results['interaction_performed']}")
    print(f"CORREGGI Clicked: {results['correggi_clicked']}")
    print(f"Overall Success: {results['success']}")
    if results['errors']:
      print(f"Errors: {', '.join(results['errors'])}")
    print("=" * 60)

    return results

  async def _perform_question_interaction(self) -> bool:
    """
    Perform interaction for the detected question type using intelligent strategy detection.

    Returns:
        True if interaction was successful, False otherwise
    """
    
    # First, try to detect question type and use appropriate strategy
    question_type = await self._detect_question_type()
    
    if question_type and question_type in self.strategies:
        print(f"🎯 Detected question type: {question_type} - using specific strategy")
        return await self._use_strategy_interaction(question_type)
    
    # Fallback to selector-based interaction
    print("🔄 Using fallback selector-based interaction")
    return await self._use_selector_interaction()

  async def _detect_question_type(self) -> Optional[str]:
    """
    Detect question type based on text content in the page.
    
    Returns:
        Detected question type or None
    """
    try:
        # Get all text content from the page
        page_text = await self.page.text_content('body')
        if not page_text:
            print("⚠️ No text content found on page")
            return None
        
        page_text_lower = page_text.lower()
        
        # Text-based question type detection
        question_type_indicators = {
            'scelta_multipla': ['scelta multipla'],
            'vero_falso': ['vero o falso'],
            'completamento_chiuso': ['completamento chiuso'],
            'trova_errore': ['trova errore'],
            'positioning': ['posizionamento'],
            'completamento_aperto': ['completamento aperto']
        }
        
        for question_type, indicators in question_type_indicators.items():
            for indicator in indicators:
                if indicator in page_text_lower:
                    print(f"🎯 Detected question type: {question_type} (found text: '{indicator}')")
                    return question_type
        
        print("⚠️ No question type indicator text found, falling back to element detection")
        return await self._detect_question_type_by_elements()
        
    except Exception as e:
        print(f"❌ Error in text-based question type detection: {e}")
        return await self._detect_question_type_by_elements()

  async def _detect_question_type_by_elements(self) -> Optional[str]:
    """
    Fallback: Detect question type based on available elements.
    
    Returns:
        Detected question type or None
    """
    # Check for positioning/drag-and-drop
    positioning_selectors = ['[draggable="true"]', '.sc-kQFRQl', 'button.sc-izXThL']
    for selector in positioning_selectors:
        elements = await self.page.query_selector_all(selector)
        if elements:
            print(f"📍 Detected positioning question with {len(elements)} draggable elements")
            return 'positioning'
    
    # Check for text inputs (completamento aperto)
    text_input_selectors = ['textarea:not([readonly])', 'input[type="text"]:not([readonly])']
    for selector in text_input_selectors:
        elements = await self.page.query_selector_all(selector)
        if elements:
            print(f"📝 Detected completamento aperto with {len(elements)} text inputs")
            return 'completamento_aperto'
    
    # Check for trova errore spans (character-level spans)
    trova_errore_selectors = ['span[data-position]', 'span.sc-ezZVYY']
    for selector in trova_errore_selectors:
        elements = await self.page.query_selector_all(selector)
        if elements and len(elements) > 10:  # Many character spans indicate trova errore
            print(f"🔍 Detected trova errore with {len(elements)} character spans")
            return 'trova_errore'
    
    # Check for choice chips (completamento chiuso)
    chip_selectors = ['.choiceChip span[role="button"]']
    for selector in chip_selectors:
        elements = await self.page.query_selector_all(selector)
        if elements:
            print(f"🔘 Detected completamento chiuso with {len(elements)} choice chips")
            return 'completamento_chiuso'
    
    # Check for radio buttons (scelta multipla)
    radio_selectors = ['input[type="radio"]']
    for selector in radio_selectors:
        elements = await self.page.query_selector_all(selector)
        if elements:
            print(f"🔘 Detected scelta multipla with {len(elements)} radio buttons")
            return 'scelta_multipla'
    
    # Check for checkboxes (could be vero/falso or multiple choice)
    checkbox_selectors = ['input[type="checkbox"]', 'label:has(input[type="checkbox"])']
    for selector in checkbox_selectors:
        elements = await self.page.query_selector_all(selector)
        if elements:
            # Try to determine if it's vero/falso by checking for grouped elements
            grouped_elements = await self._group_checkbox_elements(elements)
            if len(grouped_elements) > 1 and all(len(group) == 2 for group in grouped_elements.values()):
                print(f"✓❌ Detected vero/falso with {len(grouped_elements)} statements")
                return 'vero_falso'
            else:
                print(f"☑️ Detected multiple choice checkboxes with {len(elements)} options")
                return 'scelta_multipla'  # Treat checkbox multiple choice as scelta_multipla
    
    return None

  async def _group_checkbox_elements(self, elements):
    """Group checkbox elements by name attribute for vero/falso detection."""
    groups = {}
    for element in elements:
        try:
            name = await element.get_attribute('name')
            if name:
                if name not in groups:
                    groups[name] = []
                groups[name].append(element)
        except Exception:
            continue
    return groups

  async def _use_strategy_interaction(self, question_type: str) -> bool:
    """
    Use specific strategy for the detected question type.
    
    Args:
        question_type: The detected question type
        
    Returns:
        True if interaction was successful, False otherwise
    """
    try:
        strategy = self.strategies[question_type]
        
        # Get elements based on question type
        elements = await self._get_elements_for_strategy(question_type)
        
        if not elements:
            print(f"No elements found for {question_type} strategy")
            return False
        
        print(f"🎯 Executing {question_type} strategy with {len(elements)} elements")
        success = await strategy.interact(elements)
        
        if success:
            print(f"✅ Successfully executed {question_type} strategy")
            await self.page.wait_for_timeout(1000)  # Small delay after interaction
        else:
            print(f"❌ Failed to execute {question_type} strategy")
        
        return success
        
    except Exception as e:
        print(f"❌ Error executing {question_type} strategy: {e}")
        return False

  async def _get_elements_for_strategy(self, question_type: str):
    """Get appropriate elements for the given strategy."""
    if question_type == 'positioning':
        selectors = ['[draggable="true"]', '.sc-kQFRQl', 'button.sc-izXThL']
    elif question_type == 'completamento_aperto':
        # Specific textareas for completamento aperto
        selectors = [
            'textarea[autocapitalize="none"][rows="1"]',  # Specific completamento aperto textareas
            'textarea:not([readonly])',  # Fallback to any textarea
            'input[type="text"]:not([readonly])'  # Final fallback
        ]
    elif question_type == 'completamento_chiuso':
        selectors = ['.choiceChip span[role="button"]']
    elif question_type == 'trova_errore':
        # Character-level spans for trova errore
        selectors = [
            'span[data-position]',  # Spans with position data (from images)
            'span.sc-ezZVYY',  # Specific class from images
            'span.sc-ezZVYY.bynLmh',  # More specific class combination
            'span[class*="sc-"][data-position]',  # Styled component spans with position
        ]
    elif question_type == 'scelta_multipla':
        # For multiple choice, prioritize labels over inputs to handle custom checkboxes
        selectors = [
            'label:has(input[type="checkbox"])',  # Custom checkbox labels (priority)
            'label:has(input[type="checkbox"][name="answers"])',
            'label[class*="sc-"]',  # Styled component labels
            'label:has(input[type="radio"])',  # Radio button labels
            'input[type="radio"]',  # Direct radio buttons (fallback)
            # Note: input[type="checkbox"] is intentionally excluded to avoid clicking hidden inputs
        ]
    elif question_type == 'vero_falso':
        selectors = ['input[type="checkbox"]', 'input[type="radio"]']
    else:
        selectors = SelectorStrategies.ANSWER_CLICK_INTERACTION
    
    for selector in selectors:
        try:
            elements = await self.page.query_selector_all(selector)
            if elements:
                print(f"🎯 Using selector '{selector}' for {question_type} - found {len(elements)} elements")
                return elements
        except Exception as e:
            print(f"Error with selector {selector}: {e}")
            continue
    
    return []

  async def _use_selector_interaction(self) -> bool:
    """
    Fallback selector-based interaction method.
    
    Returns:
        True if interaction was successful, False otherwise
    """
    answer_click_selector = SelectorStrategies.ANSWER_CLICK_INTERACTION

    for selector in answer_click_selector:
      try:
        elements = await self.page.query_selector_all(selector)

        if elements:
          print(f"📍 Found {len(elements)} answer elements with selector '{selector}' - interacting...")

          # Randomly select one of the available answers
          element = random.choice(elements)

          is_visible = await element.is_visible()
          is_enabled = await element.is_enabled()

          if is_visible or is_enabled:
            text_content = await element.text_content()
            print(f"📍 Clicking on answer element: '{text_content}'")

            # Scroll into view and click
            await element.scroll_into_view_if_needed()
            await self.page.wait_for_timeout(500)
            await element.click()

            print("✅ Successfully interacted with answer element")
            return True
          else:
            print(f"Element found but not clickable (visible: {is_visible}, enabled: {is_enabled})")

      except Exception as e:
        print(f"Error with selector {selector}: {e}")
        continue

    """
        if question_type not in self.strategies:
            print(f"No strategy available for question type: {question_type}")
            return False
        
        try:
            print(f"🎯 Performing {question_type} interaction...")
            
            # Get interaction elements
            elements = await self.detector.get_interaction_elements(question_type)
            
            if not elements:
                print(f"No interaction elements found for {question_type}")
                return False
            
            # Execute the appropriate strategy
            strategy = self.strategies[question_type]
            success = await strategy.interact(elements)
            
            if success:
                print(f"✅ Successfully interacted with {question_type} question")
                # Small delay after interaction
                await self.page.wait_for_timeout(1000)
            else:
                print(f"❌ Failed to interact with {question_type} question")
            
            return success
            
        except Exception as e:
            print(f"❌ Error performing {question_type} interaction: {e}")
            return False
      """

  async def _click_correggi_esercizio(self) -> bool:
    """
    Click the "CORREGGI ESERCIZIO" button to reveal answers.
    Handles cases where button becomes disabled after interactions.

    Returns:
        True if button was clicked successfully, False otherwise
    """
    print("🔍 Looking for CORREGGI ESERCIZIO button...")

    # First, wait a bit for any DOM changes to settle after interactions
    await self.page.wait_for_timeout(1000)

    # Try multiple times with increasing wait periods
    max_attempts = 5
    for attempt in range(max_attempts):
        print(f"🔄 Attempt {attempt + 1}/{max_attempts} to find enabled CORREGGI button...")
        
        for selector in self.correggi_selectors:
            try:
                # Wait for button to be available
                button = await self.page.wait_for_selector(selector, timeout=2000)

                if button:
                    # Check if button is visible and enabled
                    is_visible = await button.is_visible()
                    is_enabled = await button.is_enabled()

                    if is_visible and is_enabled:
                        button_text = await button.text_content()
                        print(f"📍 Found enabled CORREGGI button: '{button_text}' - clicking...")

                        # Scroll into view and click
                        await button.scroll_into_view_if_needed()
                        await self.page.wait_for_timeout(500)
                        await button.click()

                        print("✅ Successfully clicked CORREGGI ESERCIZIO button")
                        return True
                    else:
                        print(f"Button found but not clickable (visible: {is_visible}, enabled: {is_enabled})")

            except PlaywrightTimeoutError:
                continue
            except Exception as e:
                print(f"Error with selector {selector}: {e}")
                continue

        # If no enabled button found, wait before next attempt
        if attempt < max_attempts - 1:
            wait_time = (attempt + 1) * 1000  # Increasing wait: 1s, 2s, 3s, 4s
            print(f"⏳ No enabled button found, waiting {wait_time}ms before next attempt...")
            await self.page.wait_for_timeout(wait_time)

    # Enhanced fallback: try to find any button with "correggi" text (case insensitive)
    print("🔄 Trying enhanced fallback search for CORREGGI button...")
    try:
        fallback_buttons = await self.page.query_selector_all('button')
        for button in fallback_buttons:
            try:
                text = await button.text_content()
                if text and 'correggi' in text.lower():
                    is_visible = await button.is_visible()
                    is_enabled = await button.is_enabled()

                    if is_visible and is_enabled:
                        print(f"📍 Found fallback CORREGGI button: '{text}' - clicking...")
                        await button.scroll_into_view_if_needed()
                        await self.page.wait_for_timeout(500)
                        await button.click()
                        print("✅ Successfully clicked fallback CORREGGI button")
                        return True
                    elif is_visible:
                        print(f"⚠️ Found disabled CORREGGI button: '{text}' - trying force click...")
                        try:
                            await button.scroll_into_view_if_needed()
                            await self.page.wait_for_timeout(500)
                            await button.click(force=True)
                            print("✅ Successfully force-clicked CORREGGI button")
                            return True
                        except Exception as force_error:
                            print(f"❌ Force click failed: {force_error}")
            except Exception:
                continue
    except Exception as e:
        print(f"Error in fallback search: {e}")

    # Final fallback: try clicking any button that might be the CORREGGI button
    print("🔄 Final fallback: trying to click any potential CORREGGI button...")
    try:
        # Look for buttons with specific classes that might be CORREGGI
        potential_selectors = [
            'button[class*="primary"]',
            'button[class*="submit"]',
            'button[class*="check"]',
            'button[class*="correct"]',
            'button[class*="sc-"]'  # Styled components
        ]
        
        for selector in potential_selectors:
            try:
                buttons = await self.page.query_selector_all(selector)
                for button in buttons:
                    try:
                        text = await button.text_content()
                        is_visible = await button.is_visible()
                        
                        # Check if this might be a CORREGGI button based on text or position
                        if is_visible and text and (
                            'correggi' in text.lower() or
                            'check' in text.lower() or
                            'submit' in text.lower() or
                            len(text.strip()) > 5  # Likely a meaningful button
                        ):
                            print(f"🎯 Trying potential CORREGGI button: '{text}' with selector '{selector}'")
                            await button.scroll_into_view_if_needed()
                            await self.page.wait_for_timeout(300)
                            await button.click(force=True)
                            print(f"✅ Successfully clicked potential CORREGGI button: '{text}'")
                            return True
                    except Exception:
                        continue
            except Exception:
                continue
    except Exception as e:
        print(f"Error in final fallback: {e}")

    print("❌ Could not find or click CORREGGI ESERCIZIO button after all attempts")
    return False

  async def _wait_for_results(self) -> None:
    """
    Wait for results to load after clicking CORREGGI ESERCIZIO.
    """
    print("⏳ Waiting for results to load...")

    # Wait for potential page changes/animations
    await self.page.wait_for_timeout(2000)

    # Try to wait for network to be idle (results loaded)
    try:
      await self.page.wait_for_load_state('networkidle', timeout=5000)
      print("✅ Results loaded (network idle)")
    except PlaywrightTimeoutError:
      print("⚠️ Network didn't go idle, but continuing...")

    # Additional wait for any animations/transitions
    await self.page.wait_for_timeout(1000)

    # Look for indicators that results are shown
    result_indicators = [
        ':has-text("Risposta sbagliata")',
        ':has-text("Risposta corretta")',
        ':has-text("La risposta esatta è")',
        ':has-text("Esercizio sbagliato")',
        '.sc-error',
        '.sc-success',
        '[class*="correct"]',
        '[class*="incorrect"]',
        '[class*="wrong"]',
        '[class*="right"]'
    ]

    results_visible = False
    for indicator in result_indicators:
      try:
        elements = await self.page.query_selector_all(indicator)
        if elements:
          visible_elements = []
          for element in elements:
            if await element.is_visible():
              visible_elements.append(element)

          if visible_elements:
            print(
              f"✅ Results visible - found {len(visible_elements)} result indicators")
            results_visible = True
            break
      except Exception:
        continue

    if not results_visible:
      print("⚠️ No clear result indicators found, but proceeding...")

    print("✅ Finished waiting for results")

  async def get_question_type_info(self, question_type: str) -> Dict[str, Any]:
    """
    Get information about a question type.

    Args:
        question_type: Question type to get info for

    Returns:
        Dictionary with question type information
    """
    return self.detector.get_question_type_info(question_type)

  async def test_interaction_elements(self, question_type: str) -> Dict[str, Any]:
    """
    Test method to check what interaction elements are available.

    Args:
        question_type: Question type to test

    Returns:
        Dictionary with test results
    """
    try:
      elements = await self.detector.get_interaction_elements(question_type)

      element_info = []
      for i, element in enumerate(elements):
        try:
          tag_name = await element.evaluate('el => el.tagName')
          is_visible = await element.is_visible()
          is_enabled = await element.is_enabled()
          text_content = await element.text_content()

          element_info.append({
              'index': i,
              'tag': tag_name,
              'visible': is_visible,
              'enabled': is_enabled,
              'text': text_content[:50] if text_content else None
          })
        except Exception as e:
          element_info.append({
              'index': i,
              'error': str(e)
          })

      return {
          'question_type': question_type,
          'total_elements': len(elements),
          'elements': element_info
      }

    except Exception as e:
      return {
          'question_type': question_type,
          'error': str(e)
      }
