"""
Content validation utilities.

This module handles validation of extracted content and quality checks.
"""

import re
from typing import Dict, List, Any, Optional, Tuple


class ContentValidator:
    """Validates extracted content quality and completeness."""
    
    def __init__(self):
        self.question_keywords = [
            'individua', 'scegli', 'indica', 'quale', 'chi', 'cosa', 'dove', 
            'quando', 'come', 'perché', 'seleziona', 'identifica', 'trova', 
            'determina', 'calcola', 'risolvi', 'osserva', 'analizza', 
            'confronta', 'descrivi', 'spiega', 'affermazioni', 'corrette'
        ]
        
        self.art_history_terms = [
            'mantegna', 'san gerolamo', 'gonzaga', 'bourbon', 'auvergne',
            'rinascimento', 'pittura', 'arte', 'artista', 'opera', 'stile',
            'leonardo', 'michelangelo', 'raffaello', 'brunelleschi', 'donatello'
        ]
        
        self.unwanted_patterns = [
            'gestisci preferenze consenso', 'cookie strettamente necessari',
            'cookie di funzionalità', 'cookie per pubblicità', 'cookie di prestazione',
            'sempre attivi', 'questi cookie sono necessari', 'accetta tutti i cookie',
            'centro preferenze sulla privacy', 'quando si visita qualsiasi sito web',
            'consenti tutti', 'rifiuta tutti', 'conferma le mie scelte',
            'copyright © zanichelli', 'supporto', 'esercizio (id)', 'difficoltà',
            'prova in autonomia', 'torna a esercizio precedente',
            'vai a esercizio successivo', 'correggi esercizio', 'termina prova'
        ]
    
    def validate_question_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate question content quality and completeness.
        
        Args:
            content: Content dictionary with 'text', 'html', and 'images'
            
        Returns:
            Validation results dictionary
        """
        validation_result = {
            'is_valid': False,
            'quality_score': 0,
            'confidence': 0.0,
            'issues': [],
            'warnings': [],
            'suggestions': [],
            'content_type': 'unknown',
            'metadata': {}
        }
        
        text = content.get('text', '')
        html = content.get('html', '')
        images = content.get('images', [])
        
        if not text:
            validation_result['issues'].append('No text content found')
            return validation_result
        
        # Basic content validation
        basic_score = self._validate_basic_content(text, validation_result)
        
        # Question-specific validation
        question_score = self._validate_question_patterns(text, validation_result)
        
        # HTML structure validation
        html_score = self._validate_html_structure(html, validation_result)
        
        # Image validation
        image_score = self._validate_images(images, validation_result)
        
        # Content type detection
        content_type = self._detect_content_type(text, html)
        validation_result['content_type'] = content_type
        
        # Calculate overall score
        total_score = basic_score + question_score + html_score + image_score
        validation_result['quality_score'] = total_score
        
        # Calculate confidence based on multiple factors
        confidence = self._calculate_confidence(text, html, images, total_score)
        validation_result['confidence'] = confidence
        
        # Determine if content is valid
        validation_result['is_valid'] = (
            total_score >= 30 and 
            confidence >= 0.6 and 
            len(validation_result['issues']) == 0
        )
        
        # Add metadata
        validation_result['metadata'] = self._extract_content_metadata(text, html, images)
        
        # Generate suggestions
        self._generate_suggestions(validation_result)
        
        return validation_result
    
    def _validate_basic_content(self, text: str, result: Dict[str, Any]) -> int:
        """Validate basic content properties."""
        score = 0
        text_lower = text.lower()
        
        # Length validation
        if len(text) < 10:
            result['issues'].append('Content too short (less than 10 characters)')
            return 0
        elif len(text) < 50:
            result['warnings'].append('Content is quite short (less than 50 characters)')
            score += 5
        else:
            score += 15
        
        # Check for unwanted content
        unwanted_found = []
        for pattern in self.unwanted_patterns:
            if pattern in text_lower:
                unwanted_found.append(pattern)
        
        if unwanted_found:
            result['issues'].append(f'Contains unwanted content: {", ".join(unwanted_found[:3])}')
            score -= 20
        else:
            score += 10
        
        # Check for meaningful content
        if len(text.split()) < 5:
            result['warnings'].append('Very few words in content')
        else:
            score += 5
        
        return max(0, score)
    
    def _validate_question_patterns(self, text: str, result: Dict[str, Any]) -> int:
        """Validate question-specific patterns."""
        score = 0
        text_lower = text.lower()
        
        # High-priority question patterns
        high_priority_patterns = [
            'individua le affermazioni corrette',
            'riferite all\'immagine',
            'si tratta del',
            'l\'autore è',
            'data in dono',
            'le rovine classiche',
            'lo sfondo è costituito',
            'è molto evidente l\'interesse'
        ]
        
        for pattern in high_priority_patterns:
            if pattern in text_lower:
                score += 25
                result['metadata']['high_priority_pattern'] = pattern
                break
        
        # Multiple choice indicators
        choice_letters = [choice for choice in ['A.', 'B.', 'C.', 'D.', 'E.', 'F.'] if choice in text]
        if choice_letters:
            score += len(choice_letters) * 5
            result['metadata']['choice_options'] = choice_letters
        
        # General question keywords
        found_keywords = [kw for kw in self.question_keywords if kw in text_lower]
        if found_keywords:
            score += len(found_keywords) * 2
            result['metadata']['question_keywords'] = found_keywords
        else:
            result['warnings'].append('No clear question keywords found')
        
        # Art history terms (for this specific domain)
        found_art_terms = [term for term in self.art_history_terms if term in text_lower]
        if found_art_terms:
            score += len(found_art_terms) * 3
            result['metadata']['art_terms'] = found_art_terms
        
        return score
    
    def _validate_html_structure(self, html: str, result: Dict[str, Any]) -> int:
        """Validate HTML structure and elements."""
        score = 0
        
        if not html:
            result['warnings'].append('No HTML content provided')
            return 0
        
        html_lower = html.lower()
        
        # Check for form elements (interactive questions)
        form_elements = ['input', 'select', 'textarea', 'button', 'label']
        found_form_elements = [elem for elem in form_elements if f'<{elem}' in html_lower]
        
        if found_form_elements:
            score += len(found_form_elements) * 3
            result['metadata']['form_elements'] = found_form_elements
        
        # Check for images
        if '<img' in html_lower:
            img_count = html_lower.count('<img')
            score += min(img_count * 2, 10)  # Cap at 10 points
            result['metadata']['html_image_count'] = img_count
        
        # Check for structured content
        structure_elements = ['div', 'p', 'span', 'h1', 'h2', 'h3']
        structure_score = sum(1 for elem in structure_elements if f'<{elem}' in html_lower)
        score += min(structure_score, 5)
        
        return score
    
    def _validate_images(self, images: List[Dict[str, Any]], result: Dict[str, Any]) -> int:
        """Validate image content."""
        score = 0
        
        if not images:
            result['warnings'].append('No images found in content')
            return 0
        
        valid_images = 0
        for img in images:
            src = img.get('src', '')
            alt = img.get('alt', '')
            
            # Check if image URL looks valid
            if src and (src.startswith('http') or src.startswith('//')):
                valid_images += 1
            
            # Bonus for descriptive alt text
            if alt and len(alt) > 5:
                score += 1
        
        score += valid_images * 3
        result['metadata']['valid_images'] = valid_images
        result['metadata']['total_images'] = len(images)
        
        return score
    
    def _detect_content_type(self, text: str, html: str) -> str:
        """Detect the type of content."""
        text_lower = text.lower()
        html_lower = html.lower()
        
        # Multiple choice
        if any(choice in text for choice in ['A.', 'B.', 'C.', 'D.']):
            if 'checkbox' in html_lower:
                return 'multiple_choice_multiple'
            else:
                return 'multiple_choice_single'
        
        # True/false
        if any(tf in text_lower for tf in ['vero', 'falso', 'true', 'false']):
            return 'true_false'
        
        # Fill in the blank
        if '____' in text or 'completa' in text_lower:
            return 'fill_blank'
        
        # Essay/open ended
        if any(essay in text_lower for essay in ['descrivi', 'spiega', 'analizza', 'confronta']):
            return 'essay'
        
        # Image-based
        if 'immagine' in text_lower or 'figura' in text_lower or '<img' in html_lower:
            return 'image_based'
        
        # Art history specific
        if any(term in text_lower for term in self.art_history_terms):
            return 'art_history'
        
        return 'general_question'
    
    def _calculate_confidence(self, text: str, html: str, images: List, score: int) -> float:
        """Calculate confidence score for the validation."""
        confidence_factors = []
        
        # Length factor
        if len(text) > 100:
            confidence_factors.append(0.8)
        elif len(text) > 50:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.3)
        
        # Question pattern factor
        text_lower = text.lower()
        if any(pattern in text_lower for pattern in [
            'individua le affermazioni corrette', 'riferite all\'immagine'
        ]):
            confidence_factors.append(0.9)
        elif any(kw in text_lower for kw in self.question_keywords):
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.4)
        
        # Structure factor
        if html and any(elem in html.lower() for elem in ['input', 'label', 'img']):
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.5)
        
        # Score factor
        if score >= 50:
            confidence_factors.append(0.9)
        elif score >= 30:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.4)
        
        # Calculate weighted average
        return sum(confidence_factors) / len(confidence_factors)
    
    def _extract_content_metadata(self, text: str, html: str, images: List) -> Dict[str, Any]:
        """Extract metadata from content."""
        metadata = {
            'word_count': len(text.split()),
            'character_count': len(text),
            'has_html': bool(html),
            'image_count': len(images),
            'estimated_difficulty': 'unknown'
        }
        
        # Estimate difficulty based on content complexity
        word_count = metadata['word_count']
        if word_count > 200:
            metadata['estimated_difficulty'] = 'high'
        elif word_count > 100:
            metadata['estimated_difficulty'] = 'medium'
        else:
            metadata['estimated_difficulty'] = 'low'
        
        # Extract question numbers if present
        question_numbers = re.findall(r'(?:question|domanda)\s*(\d+)', text.lower())
        if question_numbers:
            metadata['question_numbers'] = [int(n) for n in question_numbers]
        
        return metadata
    
    def _generate_suggestions(self, result: Dict[str, Any]) -> None:
        """Generate suggestions for improving content quality."""
        if result['quality_score'] < 20:
            result['suggestions'].append('Content quality is very low - consider manual review')
        
        if result['confidence'] < 0.5:
            result['suggestions'].append('Low confidence in content extraction - verify manually')
        
        if not result['metadata'].get('question_keywords'):
            result['suggestions'].append('No clear question indicators found - verify this is a question')
        
        if result['metadata'].get('image_count', 0) == 0 and 'immagine' in result.get('text', '').lower():
            result['suggestions'].append('Text mentions images but none were found - check image extraction')
        
        if result['content_type'] == 'unknown':
            result['suggestions'].append('Could not determine question type - may need special handling')
    
    def validate_exercise_info(self, exercise_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate exercise information.
        
        Args:
            exercise_info: Exercise information dictionary
            
        Returns:
            Validation results
        """
        validation = {
            'is_valid': True,
            'issues': [],
            'warnings': []
        }
        
        # Check required fields
        required_fields = ['title', 'number', 'clean_name']
        for field in required_fields:
            if field not in exercise_info or not exercise_info[field]:
                validation['issues'].append(f'Missing required field: {field}')
                validation['is_valid'] = False
        
        # Validate exercise number
        if 'number' in exercise_info:
            try:
                num = int(exercise_info['number'])
                if num < 1 or num > 100:  # Reasonable range
                    validation['warnings'].append(f'Exercise number {num} seems unusual')
            except (ValueError, TypeError):
                validation['issues'].append('Exercise number is not a valid integer')
                validation['is_valid'] = False
        
        # Validate title
        if 'title' in exercise_info:
            title = exercise_info['title']
            if len(title) < 3:
                validation['warnings'].append('Exercise title is very short')
            elif title == 'unknown_exercise':
                validation['warnings'].append('Exercise title was not extracted properly')
        
        return validation
    
    def get_validation_summary(self, validation_result: Dict[str, Any]) -> str:
        """
        Get a human-readable summary of validation results.
        
        Args:
            validation_result: Validation results dictionary
            
        Returns:
            Summary string
        """
        summary = []
        
        # Overall status
        status = "✓ VALID" if validation_result['is_valid'] else "✗ INVALID"
        summary.append(f"Status: {status}")
        
        # Quality metrics
        score = validation_result.get('quality_score', 0)
        confidence = validation_result.get('confidence', 0.0)
        summary.append(f"Quality Score: {score}/100")
        summary.append(f"Confidence: {confidence:.1%}")
        
        # Content type
        content_type = validation_result.get('content_type', 'unknown')
        summary.append(f"Content Type: {content_type}")
        
        # Issues and warnings
        issues = validation_result.get('issues', [])
        warnings = validation_result.get('warnings', [])
        
        if issues:
            summary.append(f"Issues ({len(issues)}):")
            for issue in issues:
                summary.append(f"  - {issue}")
        
        if warnings:
            summary.append(f"Warnings ({len(warnings)}):")
            for warning in warnings:
                summary.append(f"  - {warning}")
        
        # Suggestions
        suggestions = validation_result.get('suggestions', [])
        if suggestions:
            summary.append(f"Suggestions ({len(suggestions)}):")
            for suggestion in suggestions:
                summary.append(f"  - {suggestion}")
        
        return "\n".join(summary)