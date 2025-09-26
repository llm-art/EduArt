"""
Content extraction utilities.

This module handles extracting question content, images, and metadata from web pages.
"""

import re
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from ..browser.selectors import SelectorStrategies


class ContentExtractor:
    """Extracts content from web pages."""
    
    def __init__(self, page: Page):
        self.page = page
        self.selectors = SelectorStrategies()
    
    async def extract_question_content(self, question_number: int) -> Dict[str, Any]:
        """
        Extract the question content (text and HTML) for the current question.
        
        Args:
            question_number: Current question number
            
        Returns:
            Dictionary with extracted content
        """
        print(f"Extracting question content for question {question_number}...")
        
        # First, wait for any cookie banners to be dismissed or hidden
        await self.page.wait_for_timeout(1000)
        
        # Hide or remove cookie banners and overlays that might interfere
        await self._remove_interfering_elements()
        
        # Wait a bit more for the page to settle
        await self.page.wait_for_timeout(500)
        
        question_content = {
            'text': '',
            'html': '',
            'images': []
        }
        
        # Try structural approach first
        content = await self._extract_with_selectors()
        
        if content and len(content['text']) > 50:
            question_content = content
        else:
            # Fallback to JavaScript-based extraction
            print("Trying JavaScript-based content extraction...")
            js_content = await self._extract_with_javascript()
            if js_content and len(js_content['text']) > 50:
                question_content = js_content
        
        # Final fallback if we still have no content
        if not question_content['text']:
            question_content['text'] = "No question content found - page may still be loading or content is in an unexpected format"
            question_content['html'] = '<div class="no-content">No content extracted</div>'
        
        print(f"Extracted {len(question_content['text'])} characters of text content")
        return question_content
    
    async def _extract_with_selectors(self) -> Dict[str, Any]:
        """Extract content using CSS selectors."""
        question_content = {
            'text': '',
            'html': '',
            'images': []
        }
        
        selectors = self.selectors.get_selectors('QUESTION_CONTENT')
        
        for selector in selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                
                for element in elements:
                    # Skip if element is hidden or has cookie-related content
                    if not await self._is_valid_content_element(element):
                        continue
                    
                    # Get text content
                    text = await element.text_content()
                    if not text or len(text.strip()) < 10:
                        continue
                    
                    # Filter out unwanted content
                    if not self._is_question_content(text):
                        continue
                    
                    # Get HTML content
                    html = await element.inner_html()
                    
                    # Check if this looks like actual question content
                    if self._score_content_quality(text) > 10:
                        if len(text) > len(question_content['text']):
                            question_content['text'] = text.strip()
                            question_content['html'] = html
                            
                            # Extract images from this content
                            question_content['images'] = await self._extract_images_from_element(element)
                            print(f"Found question content using selector: {selector}")
                            break
                            
            except Exception as e:
                print(f"Error with question content selector {selector}: {e}")
                continue
        
        return question_content
    
    async def _extract_with_javascript(self) -> Dict[str, Any]:
        """Extract content using JavaScript evaluation."""
        try:
            extracted_content = await self.page.evaluate('''
                () => {
                    // Remove cookie banners and overlays first
                    const cookieSelectors = [
                        '[id*="onetrust"]', '[class*="onetrust"]', '[class*="ot-"]',
                        '[id*="cookie"]', '[class*="cookie"]', '[class*="consent"]'
                    ];
                    cookieSelectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach(el => el.remove());
                    });
                    
                    // Helper function to check if element contains text
                    function containsText(element, text) {
                        return element.textContent && element.textContent.toLowerCase().includes(text.toLowerCase());
                    }
                    
                    // Helper function to score content quality
                    function scoreContent(text) {
                        let score = 0;
                        const textLower = text.toLowerCase();
                        
                        // High priority: Question text patterns
                        if (textLower.includes('individua le affermazioni corrette')) score += 100;
                        if (textLower.includes('riferite all\\'immagine')) score += 100;
                        
                        // Multiple choice indicators
                        const choices = (text.match(/[A-F]\\./g) || []).length;
                        score += choices * 20;
                        
                        // Question keywords
                        const questionWords = ['individua', 'scegli', 'quale', 'affermazioni', 'corrette'];
                        questionWords.forEach(word => {
                            if (textLower.includes(word)) score += 10;
                        });
                        
                        // Art history terms
                        const artTerms = ['mantegna', 'san gerolamo', 'gonzaga', 'rinascimento', 'pittura'];
                        artTerms.forEach(term => {
                            if (textLower.includes(term)) score += 5;
                        });
                        
                        // Length bonus
                        if (text.length > 100) score += 10;
                        if (text.length > 300) score += 20;
                        
                        return score;
                    }
                    
                    let bestContent = { text: '', html: '', score: 0 };
                    
                    // Find all divs and check for question content
                    const allDivs = document.querySelectorAll('div');
                    allDivs.forEach(div => {
                        const text = div.textContent || '';
                        const html = div.innerHTML || '';
                        
                        // Skip if too short or contains unwanted content
                        if (text.length < 20) return;
                        if (text.toLowerCase().includes('cookie')) return;
                        if (text.toLowerCase().includes('consenso')) return;
                        if (text.toLowerCase().includes('copyright')) return;
                        if (text.toLowerCase().includes('zanichelli')) return;
                        
                        const score = scoreContent(text);
                        
                        // Update best content if this scores higher
                        if (score > bestContent.score && score > 10) {
                            bestContent = { text: text.trim(), html: html, score: score };
                        }
                    });
                    
                    return bestContent;
                }
            ''')
            
            if extracted_content and extracted_content['text']:
                return {
                    'text': extracted_content['text'],
                    'html': extracted_content['html'],
                    'images': []
                }
                
        except Exception as e:
            print(f"Error with JavaScript content extraction: {e}")
        
        return None
    
    async def _is_valid_content_element(self, element) -> bool:
        """Check if an element is valid for content extraction."""
        try:
            is_visible = await element.is_visible()
            if not is_visible:
                return False
            
            # Check if element contains cookie-related classes or IDs
            element_html = await element.get_attribute('outerHTML')
            if element_html and any(cookie_term in element_html.lower() for cookie_term in [
                'cookie', 'consent', 'onetrust', 'ot-', 'privacy-banner', 'gdpr'
            ]):
                return False
            
            return True
        except:
            return False
    
    def _is_question_content(self, text: str) -> bool:
        """Check if text appears to be question content."""
        text_lower = text.lower()
        
        # Filter out cookie banner text
        cookie_phrases = [
            'gestisci preferenze consenso', 'cookie strettamente necessari',
            'cookie di funzionalità', 'cookie per pubblicità', 'cookie di prestazione',
            'sempre attivi', 'questi cookie sono necessari', 'accetta tutti i cookie',
            'centro preferenze sulla privacy', 'quando si visita qualsiasi sito web',
            'consenti tutti', 'rifiuta tutti', 'conferma le mie scelte'
        ]
        
        if any(cookie_phrase in text_lower for cookie_phrase in cookie_phrases):
            return False
        
        # Filter out exercise title content only if it's standalone
        if any(title_phrase in text_lower for title_phrase in [
            'la pittura rinascimentale', 'pittura rinascimentale'
        ]) and len(text.strip()) < 100 and not any(question_word in text_lower for question_word in [
            'individua', 'scegli', 'quale', 'affermazioni', 'corrette', 'immagine'
        ]):
            return False
        
        # Filter out navigation and UI elements
        ui_phrases = [
            'prova in autonomia', 'esercizi', 'torna a esercizio precedente',
            'vai a esercizio successivo', 'correggi esercizio', 'termina prova',
            'copyright © zanichelli', 'supporto', 'esercizio (id)', 'difficoltà'
        ]
        
        if any(ui_phrase in text_lower for ui_phrase in ui_phrases):
            return False
        
        return True
    
    def _score_content_quality(self, text: str) -> int:
        """Score the quality of content for question extraction."""
        score = 0
        text_lower = text.lower()
        
        # Priority 1: Look for specific question patterns
        if any(keyword in text_lower for keyword in [
            'individua le affermazioni corrette', 'riferite all\'immagine',
            'si tratta del', 'l\'autore è', 'data in dono', 'le rovine classiche',
            'lo sfondo è costituito', 'è molto evidente l\'interesse'
        ]):
            score += 100
        
        # Priority 2: Look for multiple choice options
        elif any(choice in text for choice in ['A.', 'B.', 'C.', 'D.', 'E.', 'F.']):
            score += 50
        
        # Priority 3: Look for general question words
        elif any(keyword in text_lower for keyword in [
            'individua', 'scegli', 'indica', 'quale', 'chi', 'cosa', 'dove', 'quando', 'come', 'perché',
            'seleziona', 'identifica', 'trova', 'determina', 'calcola', 'risolvi',
            'osserva', 'analizza', 'confronta', 'descrivi', 'spiega', 'affermazioni', 'corrette'
        ]):
            score += 30
        
        # Priority 4: Look for art history specific terms
        elif any(keyword in text_lower for keyword in [
            'mantegna', 'san gerolamo', 'gonzaga', 'bourbon', 'auvergne',
            'rinascimento', 'pittura', 'arte', 'artista', 'opera', 'stile',
            'leonardo', 'michelangelo', 'raffaello', 'brunelleschi', 'donatello'
        ]) and len(text.strip()) > 50:
            score += 20
        
        # Length bonus
        if len(text.strip()) > 100:
            score += 10
        
        return score
    
    async def _extract_images_from_element(self, element) -> List[Dict[str, str]]:
        """Extract image information from an element."""
        image_info = []
        
        try:
            images = await element.query_selector_all('img')
            for img in images:
                try:
                    src = await img.get_attribute('src')
                    alt = await img.get_attribute('alt') or ''
                    
                    if src and not any(skip_term in src.lower() for skip_term in [
                        'icon', 'logo', 'button', 'arrow', 'spinner'
                    ]):
                        # Convert relative URLs to absolute
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            base_url = self.page.url
                            src = urljoin(base_url, src)
                        elif not src.startswith('http'):
                            base_url = self.page.url
                            src = urljoin(base_url, src)
                        
                        image_info.append({
                            'src': src,
                            'alt': alt
                        })
                except:
                    continue
        except:
            pass
        
        return image_info
    
    async def _remove_interfering_elements(self):
        """Remove elements that might interfere with content extraction."""
        try:
            await self.page.evaluate('''
                () => {
                    // Hide common cookie banner elements
                    const cookieSelectors = [
                        '[id*="cookie"]', '[class*="cookie"]', '[data-testid*="cookie"]',
                        '[id*="consent"]', '[class*="consent"]', '[data-testid*="consent"]',
                        '.ot-sdk-container', '#onetrust-consent-sdk', '.ot-fade-in',
                        '[id*="onetrust"]', '[class*="onetrust"]', '[class*="ot-"]'
                    ];
                    
                    cookieSelectors.forEach(selector => {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            if (el) {
                                el.style.display = 'none';
                                el.style.visibility = 'hidden';
                                el.remove();
                            }
                        });
                    });
                }
            ''')
        except Exception as e:
            print(f"Error removing interfering elements: {e}")
    
    async def detect_question_images(self) -> List[Dict[str, Any]]:
        """
        Detect images in the current question.
        
        Returns:
            List of image information dictionaries
        """
        print("Detecting images in current question...")
        
        selectors = self.selectors.get_selectors('QUESTION_IMAGES')
        found_images = []
        
        for selector in selectors:
            try:
                images = await self.page.query_selector_all(selector)
                for img in images:
                    try:
                        # Get image source
                        src = await img.get_attribute('src')
                        if not src:
                            continue
                        
                        # Skip data URLs, very small images, and UI elements
                        if (src.startswith('data:') or
                            'icon' in src.lower() or
                            'logo' in src.lower() or
                            'button' in src.lower()):
                            continue
                        
                        # Get image dimensions to filter out small UI elements
                        try:
                            width = await img.get_attribute('width')
                            height = await img.get_attribute('height')
                            
                            # Skip very small images (likely UI elements)
                            if width and height:
                                w, h = int(width), int(height)
                                if w < 50 or h < 50:
                                    continue
                        except:
                            pass
                        
                        # Convert relative URLs to absolute
                        src = self._normalize_url(src)
                        
                        # Check if we already found this image
                        if src not in [img_info['src'] for img_info in found_images]:
                            # Get alt text for better naming
                            alt = await img.get_attribute('alt') or ''
                            
                            found_images.append({
                                'src': src,
                                'alt': alt,
                                'element': img
                            })
                            
                    except Exception as e:
                        print(f"Error processing image: {e}")
                        continue
                        
            except Exception as e:
                print(f"Error with image selector {selector}: {e}")
                continue
        
        print(f"Found {len(found_images)} images in current question")
        return found_images
    
    def _normalize_url(self, src: str) -> str:
        """Normalize a URL to be absolute."""
        if src.startswith('//'):
            return 'https:' + src
        elif src.startswith('/'):
            base_url = self.page.url
            return urljoin(base_url, src)
        elif not src.startswith('http'):
            base_url = self.page.url
            return urljoin(base_url, src)
        return src
    
    async def get_exercise_info(self, exercise_index: Optional[int] = None) -> Dict[str, Any]:
        """
        Extract exercise information including title and number.
        
        Args:
            exercise_index: Exercise index (0-based) if known
            
        Returns:
            Dictionary with exercise information
        """
        print("Extracting exercise information from page...")
        
        # If exercise_index is provided, use it to determine the exercise number
        if exercise_index is not None:
            exercise_number = exercise_index + 1  # Convert 0-based to 1-based
        else:
            exercise_number = 1  # Default fallback
        
        exercise_info = {
            'title': 'unknown_exercise',
            'number': exercise_number,
            'clean_name': f'exercise_{exercise_number}'
        }
        
        # Look for exercise title
        title_selectors = self.selectors.get_selectors('EXERCISE_TITLE')
        
        for selector in title_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    text = await element.text_content()
                    if text and text.strip():
                        text_lower = text.lower()
                        # Look for exercise-related content
                        if any(keyword in text_lower for keyword in [
                            'pittura', 'rinascimento', 'rinascimentale', 'arte', 'esercizio'
                        ]):
                            clean_text = self._clean_title_text(text.strip())
                            
                            if 5 <= len(clean_text) <= 100:
                                exercise_info['title'] = clean_text
                                print(f"Found exercise title: {clean_text}")
                                break
                                
            except Exception as e:
                print(f"Error with title selector {selector}: {e}")
                continue
        
        # Try to extract exercise number from URL
        try:
            url = self.page.url
            patterns = [
                r'exercise[_-]?(\d+)',
                r'esercizio[_-]?(\d+)',
                r'ex[_-]?(\d+)',
                r'/(\d+)/',
                r'_(\d+)_',
                r'-(\d+)-'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url, re.IGNORECASE)
                if match:
                    exercise_info['number'] = int(match.group(1))
                    print(f"Found exercise number from URL: {exercise_info['number']}")
                    break
                    
        except Exception as e:
            print(f"Error extracting exercise number: {e}")
        
        # Create clean name combining title and number
        exercise_info['clean_name'] = f"{exercise_info['number']}_{exercise_info['title']}"
        
        print(f"Exercise info: {exercise_info}")
        return exercise_info
    
    def _clean_title_text(self, text: str) -> str:
        """Clean title text for use in filenames."""
        # Remove invalid characters for directory names
        clean_text = text.replace('/', '_').replace('\\', '_').replace(':', '_')
        clean_text = clean_text.replace('<', '_').replace('>', '_').replace('|', '_')
        clean_text = clean_text.replace('?', '_').replace('*', '_').replace('"', '_')
        clean_text = clean_text.replace(' ', '_').lower()
        
        return clean_text