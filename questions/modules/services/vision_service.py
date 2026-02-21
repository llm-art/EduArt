"""Vision model service for question analysis and text extraction."""

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..core.exceptions import VisionModelError, ConfigurationError
from ..core.types import QuestionData, QuestionType, AICallMetadata
from ..models import create_vision_model
from ..config import Config


class VisionModelService:
    """Service for vision model operations using Qwen or Gemini models."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize vision model service."""
        self.config = config or Config
        self.vision_model = None
        self._is_loaded = False
        self.prompt_manager = None  # Will be set by dependency injection
        self.ai_calls: List[AICallMetadata] = []  # Track AI calls
    
    def load_model(self) -> None:
        """Load the configured vision model (Qwen or Gemini)."""
        if self._is_loaded:
            return
            
        try:
            print(f"Loading vision model: {self.config.MODEL_TYPE}")
            
            self.vision_model = create_vision_model()
            self.vision_model.load_model()
            
            model_info = self.vision_model.get_model_info()
            print(f"✅ Vision model loaded: {model_info.get('model_name', 'Unknown')}")
            
            self._is_loaded = True
            
        except Exception as e:
            raise VisionModelError(f"Failed to load vision model: {e}")
    
    def set_prompt_manager(self, prompt_manager):
        """Set the prompt manager for this service."""
        self.prompt_manager = prompt_manager
    
    def chat(self, image_path: str, system_prompt: str, user_prompt: str,
             description: str = "AI call", max_tokens: Optional[int] = None) -> str:
        """
        Call the configured vision model with image and text prompts.
        
        Args:
            image_path: Path to the image to analyze
            system_prompt: System prompt for the model
            user_prompt: User prompt with instructions
            description: Description of the AI call for metadata tracking
            max_tokens: Optional maximum tokens for response (overrides config)
            
        Returns:
            Generated text response
            
        Raises:
            VisionModelError: If vision model processing fails
        """
        if not self._is_loaded:
            self.load_model()
        
        start_time = time.time()
        
        try:
            # Calculate input tokens (rough estimation)
            input_text = f"{system_prompt}\n{user_prompt}"
            input_tokens = self._estimate_tokens(input_text)
            
            # Call the model with optional max_tokens override
            if max_tokens is not None:
                response = self.vision_model.chat(image_path, system_prompt, user_prompt, max_tokens=max_tokens)
            else:
                response = self.vision_model.chat(image_path, system_prompt, user_prompt)
            
            # Calculate processing time and output tokens
            processing_time = time.time() - start_time
            output_tokens = self._estimate_tokens(response) if response else 0
            total_tokens = input_tokens + output_tokens
            
            # Get model info
            model_info = self.vision_model.get_model_info()
            model_name = model_info.get('model_name', 'Unknown')
            provider = model_info.get('provider', '')
            extended_model_name = f"{provider} {model_name}".strip() if provider else model_name
            
            # Create AI call metadata
            ai_call = AICallMetadata(
                description=description,
                model_name=extended_model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                processing_time=processing_time,
                timestamp=datetime.now().isoformat()
            )
            
            # Store the call metadata
            self.ai_calls.append(ai_call)
            
            return response
            
        except Exception as e:
            # Still track failed calls
            processing_time = time.time() - start_time
            model_info = self.vision_model.get_model_info() if self.vision_model else {}
            model_name = model_info.get('model_name', 'Unknown')
            provider = model_info.get('provider', '')
            extended_model_name = f"{provider} {model_name}".strip() if provider else model_name
            
            ai_call = AICallMetadata(
                description=f"{description} (failed)",
                model_name=extended_model_name,
                input_tokens=self._estimate_tokens(f"{system_prompt}\n{user_prompt}"),
                output_tokens=0,
                total_tokens=self._estimate_tokens(f"{system_prompt}\n{user_prompt}"),
                processing_time=processing_time,
                timestamp=datetime.now().isoformat()
            )
            self.ai_calls.append(ai_call)
            
            raise VisionModelError(f"Vision model chat failed: {e}")
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        # Rough estimation: ~4 characters per token for most models
        return len(text) // 4
    
    def get_ai_calls(self) -> List[AICallMetadata]:
        """Get all AI call metadata."""
        return self.ai_calls.copy()
    
    def clear_ai_calls(self) -> None:
        """Clear AI call metadata."""
        self.ai_calls.clear()
    
    def detect_question_type_from_text(self, text_content: str) -> Dict[str, Any]:
        """
        Detect question type from text content by looking for Italian keywords.
        
        Args:
            text_content: Text content to analyze
            
        Returns:
            Dictionary containing question type
        """
        # Map of Italian keywords to question types
        keyword_mapping = {
            "Scelta multipla": "multiple_choice",
            "Vero o falso": "true_false",
            "Completamento chiuso": "completion_closed",
            "Completamento aperto": "completion_open",
            "Trova errore": "select_errors",
            "Posizionamento": "positioning"
        }
        
        # Check for each keyword in the text
        for keyword, question_type in keyword_mapping.items():
            if keyword in text_content:
                print(f"Detected question type from text: {question_type} (keyword: '{keyword}')")
                return {"type": question_type}
        
        print(f"Warning: Could not detect question type from text, defaulting to unknown")
        return {"type": "unknown"}
    
    def extract_question_type(self, image_path: Path, ocr_text: str,
                            html_text: str) -> Dict[str, Any]:
        """
        Extract question type using vision model.
        
        Args:
            image_path: Path to the question image
            ocr_text: OCR extracted text
            html_text: HTML content text
            
        Returns:
            Dictionary containing question type and metadata
            
        Raises:
            VisionModelError: If type extraction fails
        """
        if not self.prompt_manager:
            raise ConfigurationError("Prompt manager not set")
        
        try:
            # Get the type extraction prompt
            user_prompt = self.prompt_manager.get_type_extraction_prompt(
                ocr_text=ocr_text,
                html_text=html_text
            )
            
            system_prompt = self.prompt_manager.get_system_prompt()
            
            # Call vision model
            response = self.chat(str(image_path), system_prompt, user_prompt, "type extraction")
            
            # Parse JSON response
            question_data = self._parse_json_response(response)
            
            question_type = question_data.get('type', 'unknown')
            print(f"Detected question type: {question_type}")
            
            return question_data
            
        except Exception as e:
            print(f"Question type extraction error: {e}")
            return {"type": "unknown", "extraction_error": str(e)}
    
    def extract_question_text(self, image_path: Path, question_type: str,
                            ocr_text: str, html_text: str) -> Dict[str, Any]:
        """
        Extract question text based on the detected type.
        
        Args:
            image_path: Path to the question image
            question_type: The detected question type
            ocr_text: OCR extracted text
            html_text: HTML content text
            
        Returns:
            Dictionary containing extracted question data
            
        Raises:
            VisionModelError: If text extraction fails
        """
        if not self.prompt_manager:
            raise ConfigurationError("Prompt manager not set")
        
        try:
            # Get the appropriate prompt for the question type
            user_prompt = self.prompt_manager.get_text_extraction_prompt(
                question_type=question_type,
                ocr_text=ocr_text,
                html_text=html_text
            )
            
            system_prompt = self.prompt_manager.get_system_prompt()
            
            # Call vision model
            response = self.chat(str(image_path), system_prompt, user_prompt, "text extraction")

            # Parse JSON response with validation for this question type
            question_data = self._parse_json_response(response, question_type)

            # Check if the LLM detected no actual question (e.g., cover page)
            if not question_data.get('has_question', True):
                reason = question_data.get('reason', 'no question detected')
                print(f"⚠️  Page has no actual question: {reason}")
                return {
                    "has_question": False,
                    "reason": reason,
                    "question_text": None,
                    "choices": [],
                    "type": question_type
                }
            
            return question_data
            
        except Exception as e:
            print(f"Question text extraction error: {e}")
            return {"text_extraction_error": str(e)}
    
    def generate_answer(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate answer for a question using the vision model.
        
        Args:
            question_data: Dictionary containing question information
            
        Returns:
            Dictionary with generated answer and metadata
        """
        try:

            
            # Format choices text
            choices_text = ""
            if question_data.get('choices'):
                choices_text = "OPTIONS:\n"
                for choice in question_data['choices']:
                    if isinstance(choice, dict):
                        choices_text += f"{choice.get('id', '?')}. {choice.get('text', '')}\n"
                    else:
                        choices_text += f"{choice}\n"
            
            # Load answer prompt template
            user_prompt = self.prompt_manager.get_answer_prompt(
                question_type=question_data.get('type', 'unknown'),
                question_title=question_data.get('question_title', ''),
                question_text=question_data.get('question_text', ''),
                language=question_data.get('language', 'it'),
                choices_text=choices_text
            )
            
            system_prompt = "You are an expert Art History student."
            
            # Get image path if available
            image_path = question_data.get('image')
            if image_path and not Path(image_path).exists():
                print(f"⚠️ Warning: Image file not found: {image_path}")
                image_path = None
            
            print(f"Generating answer for question {question_data.get('question', '?')}...")
            print(f"Question type: {question_data.get('type', 'unknown')}")
            print(f"Using image: {'Yes' if image_path else 'No'}")
            
            # Generate answer using vision model
            response = self.chat(
                image_path=image_path or "",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                description="answer generation"
            )
            
            # Clean and format the response
            answer = self._clean_response(response, question_data.get('type'))
            
            print(f"Raw LLM response: {response}")
            print(f"Cleaned answer: {answer}")
            
            # Get model info
            model_info = self.vision_model.get_model_info() if self.vision_model else {}
            model_name = model_info.get('model_name', 'Unknown')
            provider = model_info.get('provider', '')
            extended_model_name = f"{provider} {model_name}".strip() if provider else model_name
            
            return {
                'success': True,
                'generated_answer': answer,
                'raw_response': response,
                'model_name': extended_model_name,
                'used_image': image_path is not None
            }
            
        except Exception as e:
            print(f"❌ Error generating answer: {e}")
            return {
                'success': False,
                'error': str(e),
                'generated_answer': None
            }
    
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

    def _repair_json(self, text: str) -> str:
        """
        Attempt to repair malformed JSON by fixing common issues.

        Args:
            text: Malformed JSON text

        Returns:
            Repaired JSON text
        """
        # Fix unescaped newlines in string values
        # This regex finds strings and escapes unescaped newlines within them
        import re

        # Try to fix unterminated strings by finding and completing them
        # This is a simple heuristic - look for unclosed quotes
        lines = text.split('\n')
        fixed_lines = []

        for line in lines:
            # If line has an odd number of unescaped quotes, it might be unterminated
            # Count quotes that aren't escaped
            quote_count = len(re.findall(r'(?<!\\)"', line))

            # If odd number of quotes, try to close the string at the end
            if quote_count % 2 == 1:
                # Find the last quote and add a closing quote before any trailing comma/brace
                line = re.sub(r'([^"\\]*)$', r'"\1', line, count=1)

            fixed_lines.append(line)

        repaired = '\n'.join(fixed_lines)

        # Replace actual newlines within string values with \n
        # This is tricky - we need to find strings and escape newlines
        repaired = repaired.replace('\n', '\\n')
        repaired = repaired.replace('\\n', '\n', 1)  # Keep structural newlines

        return repaired

    def _parse_json_response(self, text: str, question_type: str = None) -> Dict[str, Any]:
        """
        Parse JSON response with schema validation.

        Args:
            text: Raw response text from vision model
            question_type: Type of question for validation (optional)

        Returns:
            Parsed and validated JSON dictionary
        """
        if isinstance(text, list):
            text = text[0] if text else ""

        if not text or text.strip() == "":
            return {"type": "unknown"}

        # Remove Markdown code block if present
        text = re.sub(r"^(?:```(?:json)?\s*)", "", text)
        text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)

        try:
            result = json.loads(text)
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"Attempting JSON repair...")

            # Try to repair common JSON issues
            try:
                repaired_text = self._repair_json(text)
                result = json.loads(repaired_text)
                print(f"✓ JSON repaired successfully")
            except Exception as repair_error:
                print(f"❌ JSON repair also failed: {repair_error}")
                return {"type": "unknown", "parsing_error": str(e)}

        # Validate schema if question type is provided
        if question_type:
            result = self._validate_schema(result, question_type)

        return result

    def _validate_schema(self, data: Dict, question_type: str) -> Dict:
        """
        Validate JSON schema and fix common issues.

        Args:
            data: Parsed JSON data
            question_type: Type of question being validated

        Returns:
            Validated and potentially corrected data
        """
        # Check required fields
        required = ['type', 'question_title', 'question_text', 'answers']
        missing_fields = [f for f in required if f not in data]
        if missing_fields:
            print(f"⚠️  WARNING: Missing required fields: {missing_fields}")

        # Type-specific validation
        if question_type in ['positioning', 'completion_closed', 'completion_open']:
            data = self._validate_placeholders(data)

        if question_type == 'completion_closed':
            data = self._validate_binary_choices(data)

        if question_type == 'select_errors':
            data = self._filter_duplicate_errors(data)

        return data

    def _validate_placeholders(self, data: Dict) -> Dict:
        """
        Validate and fix placeholder format to ensure [A], [B], etc.

        Args:
            data: Question data dictionary

        Returns:
            Data with corrected placeholders
        """
        question_text = data.get('question_text', '')

        # Check for [A] format
        if not re.search(r'\[A\]', question_text):
            print("⚠️  WARNING: Placeholders not in [A] format, attempting auto-fix...")

            # Fix common issues for letters A-H
            for letter in 'ABCDEFGH':
                # Fix standalone letters: A -> [A]
                question_text = re.sub(rf'\b{letter}\b(?!\])', f'[{letter}]', question_text)
                # Fix curly braces: {A} -> [A]
                question_text = re.sub(rf'\{{{letter}\}}', f'[{letter}]', question_text)
                # Fix parentheses: (A) -> [A]
                question_text = re.sub(rf'\({letter}\)', f'[{letter}]', question_text)

            data['question_text'] = question_text
            print(f"✓ Fixed placeholder format")

        return data

    def _validate_binary_choices(self, data: Dict) -> Dict:
        """
        Validate completion_closed has exactly 2 options per choice.

        Args:
            data: Question data dictionary

        Returns:
            Data (warnings printed for violations)
        """
        choices = data.get('choices', [])

        for choice in choices:
            if isinstance(choice, dict) and 'options' in choice:
                if len(choice['options']) != 2:
                    print(f"⚠️  WARNING: Choice {choice.get('id')} has {len(choice['options'])} options (expected 2)")

        return data

    def _filter_duplicate_errors(self, data: Dict) -> Dict:
        """
        Filter select_errors pairs where error == correct (not real errors).

        Args:
            data: Question data dictionary

        Returns:
            Data with duplicate error-correction pairs removed
        """
        answers = data.get('answers', [])
        original_count = len(answers)

        filtered = []
        for pair in answers:
            if isinstance(pair, dict):
                error = pair.get('error', '').strip().lower()
                correct = pair.get('correct', '').strip().lower()

                if error == correct:
                    print(f"⚠️  Skipping duplicate: error==correct=='{pair.get('error')}'")
                elif error and correct:
                    filtered.append(pair)

        data['answers'] = filtered

        if len(filtered) != original_count:
            print(f"✓ Filtered select_errors: {original_count} → {len(filtered)} pairs")

        return data
    
    def process_question_with_detected_type(self, image_path: str, ocr_text: str, html_text: str,
                        question_type: str, exercise: int, question: int, track_metadata: bool = True) -> QuestionData:
        """
        Complete question processing pipeline with pre-detected question type.
        
        This skips the LLM call for type detection and uses the provided type directly.
        
        Args:
            image_path: Path to the question image
            ocr_text: OCR extracted text
            html_text: HTML content text
            question_type: Pre-detected question type
            exercise: Exercise number
            question: Question number
            track_metadata: Whether to track AI call metadata
            
        Returns:
            Structured QuestionData object
            
        Raises:
            VisionModelError: If processing fails
        """
        try:
            # Clear previous AI calls for this question
            if track_metadata:
                self.clear_ai_calls()
            
            # Step 1: Use provided question type (no LLM call needed)
            type_data = {"type": question_type}
            
            # Step 2: Extract question text based on type
            text_data = self.extract_question_text(
                image_path, question_type, ocr_text, html_text
            )

            if 'radio' in text_data['type'] or 'check' in text_data['type']:
              question_type = text_data['type']

            # Construct image path: raw/X/screenshot/Y.png -> raw/X/imgs/Y.jpg
            question_image = Path(str(image_path).replace(".png", ".jpg").replace("/screenshot/", "/imgs/"))
            
            # Step 3: Combine data into QuestionData object
            combined_data = {**type_data, **text_data}
            
            # Get AI call metadata if tracking is enabled
            ai_calls = self.get_ai_calls() if track_metadata else []
            
            question_data = QuestionData(
                exercise=exercise,
                question=question,
                type=question_type,
                answers=combined_data.get('answers'),
                question_title=combined_data.get('question_title'),
                question_text=combined_data.get('question_text'),
                choices=combined_data.get('choices'),
                image_path=str(question_image) if question_image.exists() else None,
                ocr_text=ocr_text,
                has_image=question_image.exists(),
                ai_calls=ai_calls
            )
            
            return question_data
            
        except Exception as e:
            raise VisionModelError(f"Question processing failed: {e}")
    
    def process_question(self, image_path: Path, ocr_text: str, html_text: str,
                        exercise: int, question: int, track_metadata: bool = True) -> QuestionData:
        """
        Complete question processing pipeline.
        
        Args:
            image_path: Path to the question image
            ocr_text: OCR extracted text
            html_text: HTML content text
            exercise: Exercise number
            question: Question number
            track_metadata: Whether to track AI call metadata
            
        Returns:
            Structured QuestionData object
            
        Raises:
            VisionModelError: If processing fails
        """
        try:
            # Clear previous AI calls for this question
            if track_metadata:
                self.clear_ai_calls()
            
            # Step 1: Extract question type
            type_data = self.extract_question_type(image_path, ocr_text, html_text)
            question_type = type_data.get('type', 'unknown')
            
            # Step 2: Extract question text based on type
            text_data = self.extract_question_text(
                image_path, question_type, ocr_text, html_text
            )

            # Construct image path: raw/X/screenshot/Y.png -> raw/X/imgs/Y.jpg
            question_image = Path(str(image_path).replace(".png", ".jpg").replace("/screenshot/", "/imgs/"))
            
            # Step 3: Combine data into QuestionData object
            combined_data = {**type_data, **text_data}
            
            # Get AI call metadata if tracking is enabled
            ai_calls = self.get_ai_calls() if track_metadata else []
            
            question_data = QuestionData(
                exercise=exercise,
                question=question,
                type=question_type,
                answers=combined_data.get('answers'),
                question_title=combined_data.get('question_title'),
                question_text=combined_data.get('question_text'),
                choices=combined_data.get('choices'),
                image_path=str(question_image) if question_image.exists() else None,
                ocr_text=ocr_text,
                has_image=question_image.exists(),
                ai_calls=ai_calls
            )
            
            return question_data
            
        except Exception as e:
            raise VisionModelError(f"Question processing failed: {e}")
    
    def is_available(self) -> bool:
        """Check if vision model service is available."""
        try:
            if not self._is_loaded:
                self.load_model()
            return True
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get vision model information."""
        if self.vision_model:
            return self.vision_model.get_model_info()
        return {
            "service": "VisionModelService",
            "model_type": self.config.MODEL_TYPE,
            "loaded": self._is_loaded
        }