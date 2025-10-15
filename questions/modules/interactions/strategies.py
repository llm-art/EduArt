"""
Question interaction strategies.

This module contains individual strategy classes for interacting with
different types of questions in a randomized manner.
"""

import random
import asyncio
from typing import List, Any, Dict, Optional
from playwright.async_api import Page, ElementHandle
from abc import ABC, abstractmethod


class InteractionStrategy(ABC):
    """Base class for question interaction strategies."""
    
    def __init__(self, page: Page):
        """
        Initialize the interaction strategy.
        
        Args:
            page: Playwright page instance
        """
        self.page = page
    
    @abstractmethod
    async def interact(self, elements: List[ElementHandle]) -> bool:
        """
        Interact with the question elements.
        
        Args:
            elements: List of DOM elements to interact with
            
        Returns:
            True if interaction was successful, False otherwise
        """
        pass
    
    async def _safe_click(self, element: ElementHandle, description: str = "element") -> bool:
        """
        Safely click an element with error handling and retries.
        
        Args:
            element: Element to click
            description: Description for logging
            
        Returns:
            True if click was successful, False otherwise
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Check if element still exists
                if not element:
                    print(f"Warning: {description} element is None")
                    return False
                
                # Ensure element is visible and enabled
                is_visible = await element.is_visible()
                is_enabled = await element.is_enabled()
                
                if not is_visible:
                    print(f"Warning: {description} is not visible (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        await self.page.wait_for_timeout(500)
                        continue
                    return False
                
                if not is_enabled:
                    print(f"Warning: {description} is not enabled (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        await self.page.wait_for_timeout(500)
                        continue
                    return False
                
                # Scroll into view and click
                await element.scroll_into_view_if_needed()
                await self.page.wait_for_timeout(200)
                
                # Try different click methods
                try:
                    await element.click()
                except Exception as click_error:
                    print(f"Standard click failed for {description}, trying force click: {click_error}")
                    await element.click(force=True)
                
                print(f"✓ Successfully clicked {description}")
                return True
                
            except Exception as e:
                print(f"❌ Error clicking {description} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await self.page.wait_for_timeout(1000)
                    continue
                
        print(f"❌ Failed to click {description} after {max_retries} attempts")
        return False
    
    async def _safe_type(self, element: ElementHandle, text: str, description: str = "input") -> bool:
        """
        Safely type text into an element with error handling and retries.
        
        Args:
            element: Element to type into
            text: Text to type
            description: Description for logging
            
        Returns:
            True if typing was successful, False otherwise
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not element:
                    print(f"Warning: {description} element is None")
                    return False
                
                await element.scroll_into_view_if_needed()
                await self.page.wait_for_timeout(200)
                
                # Focus the element
                await element.click()
                await self.page.wait_for_timeout(100)
                
                # Clear existing content and type new text
                await element.select_all()
                await element.press('Delete')
                await element.type(text, delay=50)  # Add small delay between keystrokes
                
                print(f"✓ Successfully typed '{text}' into {description}")
                return True
                
            except Exception as e:
                print(f"❌ Error typing into {description} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await self.page.wait_for_timeout(500)
                    continue
                
        print(f"❌ Failed to type into {description} after {max_retries} attempts")
        return False
    
    async def _safe_get_elements(self, selectors: list, description: str = "elements") -> list:
        """
        Safely get elements with fallback selectors.
        
        Args:
            selectors: List of selectors to try
            description: Description for logging
            
        Returns:
            List of found elements
        """
        for selector in selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    print(f"Found {len(elements)} {description} using selector: {selector}")
                    return elements
            except Exception as e:
                print(f"Error with selector {selector}: {e}")
                continue
        
        print(f"No {description} found with any selector")
        return []


class SceltaMultiplaStrategy(InteractionStrategy):
    """Strategy for multiple choice questions with radio buttons or checkboxes."""
    
    async def interact(self, elements: List[ElementHandle]) -> bool:
        """
        Click a random multiple choice option (prioritizing labels over hidden inputs).
        
        Args:
            elements: List of multiple choice elements (inputs or labels)
            
        Returns:
            True if interaction was successful, False otherwise
        """
        if not elements:
            print("No multiple choice elements found for scelta multipla")
            return False
        
        print(f"Found {len(elements)} multiple choice options")
        
        # Separate labels from inputs and prioritize labels
        label_elements = []
        input_elements = []
        
        for element in elements:
            try:
                tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                if tag_name == 'label':
                    label_elements.append(element)
                else:
                    input_elements.append(element)
            except Exception as e:
                print(f"Error checking element tag: {e}")
                continue
        
        print(f"📊 Found {len(label_elements)} labels and {len(input_elements)} inputs")
        
        # Filter for available elements, prioritizing labels
        available_elements = []
        
        # First, try labels (preferred for custom checkboxes)
        for element in label_elements:
            try:
                is_visible = await element.is_visible()
                if is_visible:
                    # Check if label contains an input
                    input_element = await element.query_selector('input')
                    if input_element:
                        print(f"✅ Found clickable label with input - this is ideal for custom checkboxes")
                    available_elements.append(element)
            except Exception as e:
                print(f"Error checking label availability: {e}")
                continue
        
        # If no labels found, fall back to inputs
        if not available_elements:
            print("🔄 No available labels found, falling back to input elements")
            for element in input_elements:
                try:
                    is_visible = await element.is_visible()
                    is_enabled = await element.is_enabled()
                    if is_visible and is_enabled:
                        available_elements.append(element)
                except Exception as e:
                    print(f"Error checking input availability: {e}")
                    continue
        
        if not available_elements:
            print("❌ No available multiple choice options found")
            return False
        
        # Select a random option
        selected_element = random.choice(available_elements)
        option_index = available_elements.index(selected_element) + 1
        
        # Get element info for logging
        try:
            tag_name = await selected_element.evaluate('el => el.tagName.toLowerCase()')
            text_content = await selected_element.text_content()
            class_name = await selected_element.get_attribute('class')
            
            element_description = f"{tag_name} option {option_index}"
            if class_name:
                element_description += f" (class: {class_name[:20]}...)" if len(class_name) > 20 else f" (class: {class_name})"
            if text_content:
                clean_text = text_content.strip()[:30]
                element_description += f" - '{clean_text}...'" if len(text_content.strip()) > 30 else f" - '{clean_text}'"
                
            print(f"🎯 Selected {element_description}")
            
        except Exception:
            element_description = f"multiple choice option {option_index}"
        
        return await self._safe_click(selected_element, element_description)


class CompletamentoChiusoStrategy(InteractionStrategy):
    """Strategy for closed completion questions with clickable chips."""
    
    async def interact(self, elements: List[ElementHandle]) -> bool:
        """
        Click random choice chips to fill in blanks.
        
        Args:
            elements: List of choice chip elements
            
        Returns:
            True if interaction was successful, False otherwise
        """
        if not elements:
            print("No choice chip elements found for completamento chiuso")
            return False
        
        print(f"Found {len(elements)} choice chip options")
        
        # Filter for visible and enabled elements
        available_elements = []
        for element in elements:
            try:
                if await element.is_visible() and await element.is_enabled():
                    available_elements.append(element)
            except Exception as e:
                print(f"Error checking element availability: {e}")
                continue
        
        if not available_elements:
            print("No available choice chip options found")
            return False
        
        # Click random chips (between 1 and min(5, total_available))
        num_clicks = random.randint(1, min(5, len(available_elements)))
        selected_elements = random.sample(available_elements, num_clicks)
        
        success_count = 0
        for i, element in enumerate(selected_elements):
            if await self._safe_click(element, f"choice chip {i+1}"):
                success_count += 1
                await self.page.wait_for_timeout(300)  # Small delay between clicks
        
        print(f"Successfully clicked {success_count}/{num_clicks} choice chips")
        return success_count > 0


class VeroFalsoStrategy(InteractionStrategy):
    """Strategy for true/false questions."""
    
    async def interact(self, elements: List[ElementHandle]) -> bool:
        """
        Click random true/false options for each statement.
        
        Args:
            elements: List of true/false radio button elements
            
        Returns:
            True if interaction was successful, False otherwise
        """
        if not elements:
            print("No true/false elements found")
            return False
        
        print(f"Found {len(elements)} true/false options")
        
        # Group elements by statement (name attribute)
        statements = {}
        for element in elements:
            try:
                name = await element.get_attribute('name')
                if name:
                    if name not in statements:
                        statements[name] = []
                    statements[name].append(element)
            except Exception as e:
                print(f"Error getting element name: {e}")
                continue
        
        if not statements:
            print("No grouped statements found")
            return False
        
        print(f"Found {len(statements)} statements to answer")
        
        success_count = 0
        for statement_name, statement_elements in statements.items():
            # Filter for available elements
            available_elements = []
            for element in statement_elements:
                try:
                    if await element.is_visible() and await element.is_enabled():
                        available_elements.append(element)
                except Exception:
                    continue
            
            if available_elements:
                # Choose random true/false for this statement
                selected_element = random.choice(available_elements)
                if await self._safe_click(selected_element, f"true/false for {statement_name}"):
                    success_count += 1
                    await self.page.wait_for_timeout(200)
        
        print(f"Successfully answered {success_count}/{len(statements)} statements")
        return success_count > 0


class PositioningStrategy(InteractionStrategy):
    """Strategy for drag and drop positioning questions."""
    
    async def interact(self, elements: List[ElementHandle]) -> bool:
        """
        Drag random elements to random blank spaces, avoiding navigation elements.
        
        Args:
            elements: List of draggable elements
            
        Returns:
            True if interaction was successful, False otherwise
        """
        if not elements:
            print("No draggable elements found for positioning")
            return False
        
        print(f"Found {len(elements)} potential draggable elements")
        
        # Filter out navigation elements that should not be clicked
        filtered_elements = []
        for element in elements:
            try:
                # Check if element is visible and enabled
                is_visible = await element.is_visible()
                is_enabled = await element.is_enabled()
                
                if not (is_visible and is_enabled):
                    continue
                
                # Check aria-label to exclude navigation elements
                aria_label = await element.get_attribute('aria-label')
                if aria_label:
                    # Exclude navigation elements
                    if any(nav_text in aria_label.lower() for nav_text in [
                        'torna a esercizio precedente',
                        'vai a esercizio successivo',
                        'esercizio',  # This will catch "Esercizio 17" etc.
                        'precedente',
                        'successivo'
                    ]):
                        print(f"⚠️ Skipping navigation element: aria-label='{aria_label}'")
                        continue
                
                # Check role to exclude tab navigation
                role = await element.get_attribute('role')
                if role == 'tab':
                    print(f"⚠️ Skipping tab navigation element: role='{role}'")
                    continue
                
                # Check href to exclude navigation links
                href = await element.get_attribute('href')
                if href == '#':
                    # This is likely a navigation link, check if it has navigation-related classes or text
                    text_content = await element.text_content()
                    if text_content and text_content.strip().isdigit():
                        print(f"⚠️ Skipping question navigation link: '{text_content.strip()}'")
                        continue
                
                # If we get here, it's likely a valid draggable element
                filtered_elements.append(element)
                
            except Exception as e:
                print(f"Error checking element: {e}")
                continue
        
        if not filtered_elements:
            print("No valid draggable elements found after filtering navigation elements")
            return False
        
        print(f"Found {len(filtered_elements)} valid draggable elements after filtering")
        
        # Find drop targets (blank spaces)
        drop_target_selectors = [
            '.sc-kQFRQl',  # Based on HTML analysis
            '[class*="blank"]',
            '[class*="drop"]',
            'button.sc-izXThL',
            '.sc-dNHLo button'
        ]
        
        drop_targets = []
        for selector in drop_target_selectors:
            try:
                targets = await self.page.query_selector_all(selector)
                # Filter drop targets to avoid navigation elements too
                for target in targets:
                    try:
                        aria_label = await target.get_attribute('aria-label')
                        if aria_label and any(nav_text in aria_label.lower() for nav_text in [
                            'torna a esercizio', 'vai a esercizio', 'precedente', 'successivo'
                        ]):
                            continue
                        if await target.is_visible():
                            drop_targets.append(target)
                    except Exception:
                        continue
            except Exception as e:
                print(f"Error finding drop targets with {selector}: {e}")
                continue
        
        if not drop_targets:
            print("No drop targets found, trying click-based interaction")
            return await self._fallback_click_interaction(filtered_elements)
        
        print(f"Found {len(drop_targets)} valid drop targets")
        
        # Perform random drag and drop operations
        num_operations = min(3, len(filtered_elements), len(drop_targets))
        success_count = 0
        
        for i in range(num_operations):
            try:
                draggable = random.choice(filtered_elements)
                target = random.choice(drop_targets)
                
                # Get bounding boxes
                drag_box = await draggable.bounding_box()
                target_box = await target.bounding_box()
                
                if drag_box and target_box:
                    # Perform drag and drop
                    await self.page.mouse.move(
                        drag_box['x'] + drag_box['width'] / 2,
                        drag_box['y'] + drag_box['height'] / 2
                    )
                    await self.page.mouse.down()
                    await self.page.wait_for_timeout(100)
                    
                    await self.page.mouse.move(
                        target_box['x'] + target_box['width'] / 2,
                        target_box['y'] + target_box['height'] / 2
                    )
                    await self.page.mouse.up()
                    
                    print(f"✓ Dragged element {i+1} to target")
                    success_count += 1
                    await self.page.wait_for_timeout(500)
                    
                    # Remove used elements to avoid duplicates
                    filtered_elements.remove(draggable)
                    drop_targets.remove(target)
                
            except Exception as e:
                print(f"Error in drag and drop operation {i+1}: {e}")
                continue
        
        print(f"Successfully completed {success_count}/{num_operations} drag operations")
        return success_count > 0
    
    async def _fallback_click_interaction(self, elements: List[ElementHandle]) -> bool:
        """Fallback to click-based interaction for positioning questions."""
        print("Using fallback click-based interaction for positioning")
        
        if not elements:
            return False
        
        # Click a few random elements (already filtered)
        num_clicks = min(2, len(elements))
        selected_elements = random.sample(elements, num_clicks)
        
        success_count = 0
        for i, element in enumerate(selected_elements):
            if await self._safe_click(element, f"positioning element {i+1}"):
                success_count += 1
                await self.page.wait_for_timeout(300)
        
        return success_count > 0


class TrovaErroreStrategy(InteractionStrategy):
    """Strategy for find errors questions with character-level span clicking."""
    
    async def interact(self, elements: List[ElementHandle]) -> bool:
        """
        Select entire words made up of multiple consecutive spans with data-position attributes.
        This approach identifies word boundaries and selects complete words for error highlighting.
        
        Args:
            elements: List of character span elements
            
        Returns:
            True if interaction was successful, False otherwise
        """
        if not elements:
            print("No character span elements found for trova errore")
            return False
        
        success = False

        # Get all spans with data-position attributes
        all_spans = await self.page.query_selector_all('span[data-position]')
        if not all_spans:
            print("No spans with data-position found")
            return False

        print(f"Found {len(all_spans)} spans with data-position")

        # Group spans into words by analyzing their positions and content
        words = await self._group_spans_into_words(all_spans)
        
        if not words:
            print("No words found from spans")
            return False

        print(f"Identified {len(words)} words from spans")

        # Select a random word to highlight
        selected_word = random.choice(words)
        word_text = ''.join([span['text'] for span in selected_word])
        word_positions = [span['position'] for span in selected_word]
        
        print(f"🎯 Selected word: '{word_text}' (positions: {word_positions[0]}-{word_positions[-1]})")

        # Double-click on a span in the middle of the word to select it and reveal pencil
        try:
            # Select middle span (or first if only one span)
            middle_index = len(selected_word) // 2
            middle_span = selected_word[middle_index]['element']
            
            print(f"🖱️ Double-clicking on middle span '{selected_word[middle_index]['text']}' at position {selected_word[middle_index]['position']}")
            
            await middle_span.scroll_into_view_if_needed()
            await self.page.wait_for_timeout(300)
            
            # Double-click to select the word
            await middle_span.dblclick()
            
            print(f"✅ Double-clicked on span '{selected_word[middle_index]['text']}' to select word '{word_text}'")
            
            # Wait for pencil button to appear
            await self.page.wait_for_timeout(1000)
            
            # Look for pencil button - be very specific to avoid navigation buttons
            pencil_selectors = [
                'button.sc-dlqFnW',  # Specific class from logs (most reliable)
                'button[aria-label*="pencil"]',  # Aria label containing pencil
                'button[title*="pencil"]',  # Title containing pencil
            ]
            
            pencil_button = None
            for selector in pencil_selectors:
                try:
                    buttons = await self.page.query_selector_all(selector)
                    for button in buttons:
                        try:
                            is_visible = await button.is_visible()
                            is_enabled = await button.is_enabled()
                            if is_visible and is_enabled:
                                # Check if it's NOT a navigation button
                                aria_label = await button.get_attribute('aria-label')
                                title = await button.get_attribute('title')
                                button_text = await button.text_content()
                                
                                # Skip navigation buttons
                                if aria_label and any(nav_text in aria_label.lower() for nav_text in [
                                    'torna', 'vai', 'precedente', 'successivo', 'back', 'next', 'esercizio'
                                ]):
                                    print(f"⚠️ Skipping navigation button: aria-label='{aria_label}'")
                                    continue
                                
                                if title and any(nav_text in title.lower() for nav_text in [
                                    'torna', 'vai', 'precedente', 'successivo', 'back', 'next', 'esercizio'
                                ]):
                                    print(f"⚠️ Skipping navigation button: title='{title}'")
                                    continue
                                
                                if button_text and any(nav_text in button_text.lower() for nav_text in [
                                    'torna', 'vai', 'precedente', 'successivo', 'back', 'next'
                                ]):
                                    print(f"⚠️ Skipping navigation button: text='{button_text.strip()}'")
                                    continue
                                
                                # Additional check: make sure it's actually a pencil/edit button
                                button_html = await button.inner_html()
                                if ('svg' in button_html.lower() and
                                    ('pencil' in button_html.lower() or
                                     'edit' in button_html.lower() or
                                     'viewBox' in button_html)):  # SVG viewBox indicates drawing icon
                                    pencil_button = button
                                    print(f"🖊️ Found valid pencil button with selector: {selector}")
                                    break
                                else:
                                    print(f"⚠️ Button has SVG but doesn't look like pencil: {selector}")
                        except Exception as e:
                            print(f"Error checking button: {e}")
                            continue
                    if pencil_button:
                        break
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
                    continue
            
            # Fallback: look for buttons that appear near the clicked word
            if not pencil_button:
                print("🔍 No specific pencil button found, looking for buttons near selected word...")
                try:
                    # Look for any button that appeared after double-clicking the word
                    all_buttons = await self.page.query_selector_all('button')
                    for button in all_buttons:
                        try:
                            is_visible = await button.is_visible()
                            is_enabled = await button.is_enabled()
                            if is_visible and is_enabled:
                                # Get button position to see if it's near our selected word
                                button_box = await button.bounding_box()
                                span_box = await middle_span.bounding_box()
                                
                                if button_box and span_box:
                                    # Check if button is reasonably close to the span (within 100px)
                                    distance = abs(button_box['x'] - span_box['x']) + abs(button_box['y'] - span_box['y'])
                                    if distance < 100:
                                        # Make sure it's not a navigation button
                                        aria_label = await button.get_attribute('aria-label')
                                        if not aria_label or not any(nav_text in aria_label.lower() for nav_text in [
                                            'torna', 'vai', 'precedente', 'successivo', 'back', 'next', 'esercizio'
                                        ]):
                                            pencil_button = button
                                            print(f"🖊️ Found nearby button (distance: {distance}px)")
                                            break
                        except Exception:
                            continue
                except Exception as e:
                    print(f"Error in fallback button search: {e}")
            
            if pencil_button:
                # Click the pencil button to highlight the error
                print(f"🖊️ Clicking pencil button for word: '{word_text}'")
                await pencil_button.scroll_into_view_if_needed()
                await self.page.wait_for_timeout(300)
                await pencil_button.click()
                
                print(f"✅ Successfully clicked pencil button for word: '{word_text}'")
                success = True
                
                # Wait for the highlight to be applied
                await self.page.wait_for_timeout(800)
                
            else:
                print(f"⚠️ No pencil button found after double-clicking word: '{word_text}'")
                success = False
                
        except Exception as e:
            print(f"❌ Error in double-click and pencil approach: {e}")
            success = False

        return success


    async def _group_spans_into_words(self, spans: List[ElementHandle]) -> List[List[Dict]]:
        """
        Group consecutive spans into words based on their positions and content.
        
        Args:
            spans: List of span elements with data-position attributes
            
        Returns:
            List of words, where each word is a list of span info dictionaries
        """
        span_data = []
        
        # Extract data from all spans
        for span in spans:
            try:
                position_str = await span.get_attribute('data-position')
                text_content = await span.text_content()
                is_visible = await span.is_visible()
                
                if position_str and text_content and is_visible:
                    try:
                        position = int(position_str)
                        span_data.append({
                            'element': span,
                            'position': position,
                            'text': text_content.strip(),
                            'is_space': text_content.strip() == '' or text_content == ' '
                        })
                    except ValueError:
                        continue
            except Exception as e:
                print(f"Error processing span: {e}")
                continue
        
        if not span_data:
            return []
        
        # Sort by position
        span_data.sort(key=lambda x: x['position'])
        
        # Group into words
        words = []
        current_word = []
        
        for span_info in span_data:
            # Skip spaces and empty spans
            if span_info['is_space'] or not span_info['text']:
                # If we have a current word, save it and start a new one
                if current_word:
                    words.append(current_word)
                    current_word = []
                continue
            
            # Check if this span continues the current word
            if current_word:
                last_position = current_word[-1]['position']
                current_position = span_info['position']
                
                # If positions are consecutive or very close, it's part of the same word
                if current_position - last_position <= 2:  # Allow small gaps
                    current_word.append(span_info)
                else:
                    # Start a new word
                    if current_word:
                        words.append(current_word)
                    current_word = [span_info]
            else:
                # Start first word
                current_word = [span_info]
        
        # Don't forget the last word
        if current_word:
            words.append(current_word)
        
        # Filter words to only include those with at least 2 characters
        filtered_words = []
        for word in words:
            word_text = ''.join([span['text'] for span in word])
            if len(word_text.strip()) >= 2:  # At least 2 characters
                filtered_words.append(word)
        
        print(f"📊 Found {len(filtered_words)} words with 2+ characters:")
        for i, word in enumerate(filtered_words[:10]):  # Show first 10 words
            word_text = ''.join([span['text'] for span in word])
            positions = [span['position'] for span in word]
            print(f"  Word {i+1}: '{word_text}' (positions: {positions[0]}-{positions[-1]})")
        
        return filtered_words


class CompletamentoApertoStrategy(InteractionStrategy):
    """Strategy for open completion questions with text inputs and textareas."""
    
    # Pool of random text for completion
    RANDOM_TEXT_POOL = [
        "test", "esempio", "prova", "sample", "demo",
        "arte", "storia", "cultura", "bellezza", "opera",
        "rinascimento", "pittura", "scultura", "architettura",
        "leonardo", "michelangelo", "raffaello", "donatello",
        "firenze", "roma", "venezia", "milano", "napoli",
        "1400", "1500", "1600", "XV", "XVI", "XVII",
        "San Gerolamo nello studio di Antonello da Messina è databile attorno al",
        "La tavola londinese mostra, al di là di un",
        "ribassato di foggia catalana, un ombroso interno"
    ]
    
    async def interact(self, elements: List[ElementHandle]) -> bool:
        """
        Type text into specific textareas (autocapitalize="none" rows="1") and lose focus.
        
        Args:
            elements: List of textarea elements
            
        Returns:
            True if interaction was successful, False otherwise
        """
        if not elements:
            print("No textarea elements found for completamento aperto")
            return False
        
        print(f"Found {len(elements)} textarea elements")
        
        # Filter for specific completamento aperto textareas
        target_textareas = []
        
        for element in elements:
            try:
                is_visible = await element.is_visible()
                is_enabled = await element.is_enabled()
                if is_visible and is_enabled:
                    # Check if it's the specific textarea we want
                    tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                    autocapitalize = await element.get_attribute('autocapitalize')
                    rows = await element.get_attribute('rows')
                    
                    if (tag_name == 'textarea' and
                        autocapitalize == 'none' and
                        rows == '1'):
                        target_textareas.append(element)
                        print(f"✓ Found target textarea: autocapitalize='{autocapitalize}', rows='{rows}'")
            except Exception as e:
                print(f"Error checking textarea element: {e}")
                continue
        
        if not target_textareas:
            print("❌ No target textareas found (autocapitalize='none' rows='1')")
            return False
        
        print(f"📊 Found {len(target_textareas)} target textareas for completamento aperto")
        
        # Select one textarea to interact with
        selected_textarea = random.choice(target_textareas)
        
        try:
            # Generate text with at least 3 characters
            short_texts = [
                "arte", "storia", "cultura", "bellezza", "opera", "pittura",
                "scultura", "leonardo", "michelangelo", "raffaello", "donatello",
                "firenze", "roma", "venezia", "milano", "napoli", "rinascimento"
            ]
            random_text = random.choice(short_texts)
            
            # Ensure at least 3 characters
            if len(random_text) < 3:
                random_text = random_text + "123"  # Fallback to ensure 3+ chars
            
            print(f"📝 Typing into completamento aperto textarea: '{random_text}' ({len(random_text)} characters)")
            
            # Focus the textarea and type text
            await selected_textarea.scroll_into_view_if_needed()
            await self.page.wait_for_timeout(300)
            await selected_textarea.click()
            await self.page.wait_for_timeout(200)
            
            # Clear existing content and type new text
            await selected_textarea.type(random_text, delay=50)
            
            print(f"✓ Successfully typed '{random_text}' into textarea")
            
            # CRITICAL: Lose focus by clicking elsewhere to enable CORREGGI ESERCIZIO button
            await self.page.wait_for_timeout(300)
            
            # Click somewhere else on the page to lose focus
            try:
                # Try clicking on the body element away from the textarea
                await self.page.click('body', position={'x': 100, 'y': 100})
                await self.page.wait_for_timeout(500)
                print("✓ Lost focus by clicking elsewhere on the page")
            except Exception as e:
                print(f"⚠️ Could not click elsewhere: {e}")
                # Fallback: press Tab
                try:
                    await self.page.keyboard.press('Tab')
                    await self.page.wait_for_timeout(300)
                    print("✓ Lost focus using Tab key")
                except Exception as tab_error:
                    print(f"⚠️ Could not lose focus: {tab_error}")
            
            print("✅ Successfully completed completamento aperto interaction")
            print("🎯 Focus has been lost - CORREGGI ESERCIZIO should now be clickable")
            return True
            
        except Exception as e:
            print(f"❌ Error interacting with completamento aperto textarea: {e}")
            return False