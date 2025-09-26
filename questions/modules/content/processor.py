"""
Content processing utilities.

This module handles processing and cleaning of extracted content.
"""

import re
from typing import Dict, List, Any, Optional
from playwright.async_api import Page


class ContentProcessor:
    """Processes and cleans extracted content."""
    
    def __init__(self, page: Page):
        self.page = page
    
    async def get_current_question_number(self) -> int:
        """
        Get the current question number from the data-index attribute.
        
        Returns:
            Current question number (1-based)
        """
        print("Getting current question number...")
        
        # Primary method: Look for the active slide with data-index
        data_index_selectors = [
            '.slick-slide.slick-active.slick-current[data-index]',
            '.slick-slide.slick-active[data-index]',
            '.slick-current[data-index]',
            '[data-index].slick-active',
            '[data-index].slick-current',
            '[data-index][class*="active"]',
            '[data-index][class*="current"]'
        ]
        
        for selector in data_index_selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=3000)
                if element:
                    data_index = await element.get_attribute('data-index')
                    if data_index is not None and data_index.isdigit():
                        # Convert 0-based index to 1-based question number
                        question_num = int(data_index) + 1
                        print(f"Current question number from data-index: {question_num} (data-index={data_index})")
                        return question_num
            except Exception as e:
                print(f"Error with data-index selector {selector}: {e}")
                continue
        
        # Fallback: Look for pagination active states
        pagination_selectors = [
            '.pagination .active',
            '.pagination .current',
            '.pagination .selected',
            '.pagination [class*="active"]',
            '.pagination button[class*="active"]',
            '.pagination a[class*="active"]'
        ]
        
        for selector in pagination_selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=3000)
                if element:
                    text = await element.text_content()
                    if text and text.strip().isdigit():
                        question_num = int(text.strip())
                        print(f"Current question number from pagination: {question_num}")
                        return question_num
            except Exception as e:
                print(f"Error with pagination selector {selector}: {e}")
                continue
        
        # Final fallback: try to find from URL
        try:
            url = self.page.url
            match = re.search(r'question[=/_](\d+)', url, re.IGNORECASE)
            if match:
                question_num = int(match.group(1))
                print(f"Found question number in URL: {question_num}")
                return question_num
        except Exception as e:
            print(f"Error extracting question from URL: {e}")
        
        print("Could not determine current question number, defaulting to 1")
        return 1
    
    async def get_total_questions(self) -> int:
        """
        Get the total number of questions from data-index attributes.
        
        Returns:
            Total number of questions
        """
        print("Getting total number of questions...")
        
        # Primary method: Look for all slides with data-index to find the highest index
        max_data_index = -1
        
        try:
            # Find all elements with data-index
            elements = await self.page.query_selector_all('[data-index]')
            for element in elements:
                data_index = await element.get_attribute('data-index')
                if data_index is not None and data_index.isdigit():
                    index = int(data_index)
                    max_data_index = max(max_data_index, index)
            
            if max_data_index >= 0:
                # Convert 0-based index to total count (add 1)
                total_questions = max_data_index + 1
                print(f"Total questions from data-index: {total_questions} (max index: {max_data_index})")
                return total_questions
                
        except Exception as e:
            print(f"Error finding total from data-index: {e}")
        
        # Fallback: Look for pagination numbers to find the highest number
        pagination_selectors = [
            '.pagination button',
            '.pagination a',
            '.pagination span',
            '[class*="pagination"] button',
            '[class*="pagination"] a',
            '[class*="pagination"] span'
        ]
        
        max_question = 0
        
        for selector in pagination_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    text = await element.text_content()
                    if text and text.strip().isdigit():
                        num = int(text.strip())
                        max_question = max(max_question, num)
            except Exception as e:
                print(f"Error with pagination selector {selector}: {e}")
                continue
        
        if max_question > 0:
            print(f"Total questions from pagination: {max_question}")
            return max_question
        
        # Final fallback: look for text indicators like "20 esercizi"
        try:
            text_indicators = await self.page.query_selector_all(':has-text("esercizi")')
            for element in text_indicators:
                text = await element.text_content()
                if text:
                    match = re.search(r'(\d+)\s*esercizi', text, re.IGNORECASE)
                    if match:
                        total = int(match.group(1))
                        print(f"Found total questions from text: {total}")
                        return total
        except Exception as e:
            print(f"Error finding total from text: {e}")
        
        print("Could not determine total questions, defaulting to 20")
        return 20
    
    async def is_last_question(self) -> bool:
        """
        Check if we're on the last question.
        
        Returns:
            True if on last question, False otherwise
        """
        try:
            current = await self.get_current_question_number()
            total = await self.get_total_questions()
            is_last = current >= total
            print(f"Question {current}/{total} - Is last: {is_last}")
            return is_last
        except Exception as e:
            print(f"Error checking if last question: {e}")
            return False
    
    def clean_content_text(self, text: str) -> str:
        """
        Clean and normalize content text.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common unwanted patterns
        unwanted_patterns = [
            r'Copyright © Zanichelli.*',
            r'Supporto.*',
            r'Difficoltà:.*',
            r'Esercizio \(ID\):.*'
        ]
        
        for pattern in unwanted_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    def extract_multiple_choice_options(self, text: str) -> List[Dict[str, str]]:
        """
        Extract multiple choice options from text.
        
        Args:
            text: Text containing multiple choice options
            
        Returns:
            List of option dictionaries
        """
        options = []
        
        # Pattern to match options like "A. Some text", "B. Other text", etc.
        pattern = r'([A-F])\.\s*([^A-F]*?)(?=[A-F]\.|$)'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for letter, content in matches:
            options.append({
                'letter': letter,
                'content': content.strip()
            })
        
        return options
    
    def identify_question_type(self, text: str, html: str) -> str:
        """
        Identify the type of question based on content.
        
        Args:
            text: Question text
            html: Question HTML
            
        Returns:
            Question type string
        """
        text_lower = text.lower()
        
        # Multiple choice indicators
        if any(choice in text for choice in ['A.', 'B.', 'C.', 'D.']):
            if 'checkbox' in html.lower():
                return 'multiple_choice_multiple'
            else:
                return 'multiple_choice_single'
        
        # True/false questions
        if any(tf in text_lower for tf in ['vero', 'falso', 'true', 'false']):
            return 'true_false'
        
        # Fill in the blank
        if '____' in text or 'completa' in text_lower:
            return 'fill_blank'
        
        # Essay/open ended
        if any(essay in text_lower for essay in ['descrivi', 'spiega', 'analizza', 'confronta']):
            return 'essay'
        
        # Image-based questions
        if 'immagine' in text_lower or 'figura' in text_lower:
            return 'image_based'
        
        return 'unknown'
    
    def extract_question_metadata(self, text: str, html: str) -> Dict[str, Any]:
        """
        Extract metadata from question content.
        
        Args:
            text: Question text
            html: Question HTML
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            'type': self.identify_question_type(text, html),
            'has_images': 'img' in html.lower(),
            'word_count': len(text.split()),
            'character_count': len(text),
            'multiple_choice_options': [],
            'keywords': []
        }
        
        # Extract multiple choice options
        if metadata['type'].startswith('multiple_choice'):
            metadata['multiple_choice_options'] = self.extract_multiple_choice_options(text)
        
        # Extract keywords (art history terms)
        art_keywords = [
            'rinascimento', 'pittura', 'mantegna', 'gonzaga', 'arte',
            'leonardo', 'michelangelo', 'raffaello', 'brunelleschi', 'donatello'
        ]
        
        text_lower = text.lower()
        metadata['keywords'] = [keyword for keyword in art_keywords if keyword in text_lower]
        
        return metadata
    
    def format_content_for_display(self, content: Dict[str, Any]) -> str:
        """
        Format content for display or saving.
        
        Args:
            content: Content dictionary
            
        Returns:
            Formatted content string
        """
        if not content.get('text'):
            return "No content available"
        
        formatted = f"Question Content:\n"
        formatted += "=" * 50 + "\n\n"
        formatted += self.clean_content_text(content['text'])
        
        if content.get('images'):
            formatted += f"\n\nImages ({len(content['images'])}):\n"
            formatted += "-" * 20 + "\n"
            for i, img in enumerate(content['images'], 1):
                formatted += f"{i}. {img.get('src', 'Unknown URL')}\n"
                if img.get('alt'):
                    formatted += f"   Alt: {img['alt']}\n"
        
        return formatted
    
    def validate_content_quality(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the quality of extracted content.
        
        Args:
            content: Content dictionary
            
        Returns:
            Validation results
        """
        validation = {
            'is_valid': False,
            'score': 0,
            'issues': [],
            'suggestions': []
        }
        
        text = content.get('text', '')
        html = content.get('html', '')
        
        # Check minimum content length
        if len(text) < 20:
            validation['issues'].append('Content too short')
        else:
            validation['score'] += 10
        
        # Check for question indicators
        question_indicators = [
            'individua', 'scegli', 'quale', 'affermazioni', 'corrette',
            'A.', 'B.', 'C.', 'D.'
        ]
        
        if any(indicator in text.lower() for indicator in question_indicators):
            validation['score'] += 20
        else:
            validation['issues'].append('No clear question indicators found')
        
        # Check for unwanted content
        unwanted_content = [
            'cookie', 'consenso', 'privacy', 'zanichelli', 'copyright'
        ]
        
        if any(unwanted in text.lower() for unwanted in unwanted_content):
            validation['issues'].append('Contains unwanted content (cookies, copyright, etc.)')
            validation['score'] -= 10
        
        # Check for images
        if content.get('images'):
            validation['score'] += 5
        
        # Overall validation
        validation['is_valid'] = validation['score'] >= 15 and len(validation['issues']) == 0
        
        if not validation['is_valid']:
            validation['suggestions'].append('Content may need manual review')
        
        return validation