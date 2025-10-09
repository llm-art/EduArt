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
             description: str = "AI call") -> str:
        """
        Call the configured vision model with image and text prompts.
        
        Args:
            image_path: Path to the image to analyze
            system_prompt: System prompt for the model
            user_prompt: User prompt with instructions
            description: Description of the AI call for metadata tracking
            
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
            
            # Call the model
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
            
            # Parse JSON response
            question_data = self._parse_json_response(response)
            
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

            
        
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """
        Parse JSON response with fallback handling.
        
        Args:
            text: Raw response text from vision model
            
        Returns:
            Parsed JSON dictionary
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
            return result
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            return {"type": "unknown", "parsing_error": "failed_json_decode"}
    
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


            
            # Step 3: Combine data into QuestionData object
            combined_data = {**type_data, **text_data}
            
            # Get AI call metadata if tracking is enabled
            ai_calls = self.get_ai_calls() if track_metadata else []
            
            question_data = QuestionData(
                exercise=exercise,
                question=question,
                type=question_type,
                question_title=combined_data.get('question_title'),
                question_text=combined_data.get('question_text'),
                choices=combined_data.get('choices'),
                image_path=str(image_path) if image_path.exists() else None,
                ocr_text=ocr_text,
                has_image=image_path.exists(),
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