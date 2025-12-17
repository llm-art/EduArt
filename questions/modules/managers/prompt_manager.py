"""Prompt manager for handling prompt templates."""

from pathlib import Path
from typing import Dict, Optional
from ..core.exceptions import FileOperationError, ConfigurationError


class PromptManager:
    """Manager for prompt templates used by vision models."""
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize prompt manager.
        
        Args:
            prompts_dir: Directory containing prompt template files.
                        Should be passed from calling script. Defaults to None for backward compatibility.
        """
        if prompts_dir is None:
            # Backward compatibility: default to project root prompts directory
            # In production, this should be passed from the calling script
            prompts_dir = Path(__file__).parent.parent.parent.parent / "prompts"
        
        self.prompts_dir = Path(prompts_dir)
        self.prompts: Dict[str, str] = {}
        self._load_prompts()
    
    def _load_prompts(self) -> None:
        """Load all prompt templates from files."""
        if not self.prompts_dir.exists():
            raise FileOperationError(f"Prompts directory not found: {self.prompts_dir}")
        
        prompt_files = {
            'system_prompt': 'system_prompt.txt',
            'extract_type': 'extract_type.txt',
            'extract_text_multiple_choice': 'extract_text_multiple_choice.txt',
            'extract_text_select_errors': 'extract_text_select_errors.txt',
            'extract_text_positioning': 'extract_text_positioning.txt',
            'extract_text_completion_open': 'extract_text_completion_open.txt',
            'extract_text_completion_closed': 'extract_text_completion_closed.txt',
            'extract_text_true_false': 'extract_text_true_false.txt',
            'answer_question': 'answer_question.txt'
        }
        
        for prompt_key, filename in prompt_files.items():
            file_path = self.prompts_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.prompts[prompt_key] = f.read().strip()
                except Exception as e:
                    print(f"Warning: Could not load prompt {filename}: {e}")
            else:
                print(f"Warning: Prompt file not found: {file_path}")
        
        print(f"Loaded {len(self.prompts)} prompt templates")
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for vision models."""
        return self.prompts.get('system_prompt', 
                               "You are an expert at analyzing educational content and extracting structured information.")
    
    def get_type_extraction_prompt(self, ocr_text: str, html_text: str) -> str:
        """
        Get prompt for question type extraction.
        
        Args:
            ocr_text: OCR extracted text
            html_text: HTML content text
            
        Returns:
            Formatted prompt for type extraction
        """
        template = self.prompts.get('extract_type', '')
        if not template:
            raise ConfigurationError("Type extraction prompt not found")
        
        return template.format(ocr_text=ocr_text, html_text=html_text)
    
    def get_text_extraction_prompt(self, question_type: str, ocr_text: str, 
                                 html_text: str) -> str:
        """
        Get prompt for question text extraction based on type.
        
        Args:
            question_type: The detected question type
            ocr_text: OCR extracted text
            html_text: HTML content text
            
        Returns:
            Formatted prompt for text extraction
        """
        # Map question types to prompt keys
        prompt_mapping = {
            'multiple_choice': 'extract_text_multiple_choice',
            'select_errors': 'extract_text_select_errors',
            'highlight_errors': 'extract_text_select_errors',  # Use same as select_errors
            'positioning': 'extract_text_positioning',
            'completion_open': 'extract_text_completion_open',
            'completion_closed': 'extract_text_completion_closed',
            'true_false': 'extract_text_true_false'
        }
        
        prompt_key = prompt_mapping.get(question_type, 'extract_text_multiple_choice')
        template = self.prompts.get(prompt_key, '')
        
        if not template:
            # Fallback to multiple choice prompt
            template = self.prompts.get('extract_text_multiple_choice', '')
            if not template:
                raise ConfigurationError(f"No prompt template found for type: {question_type}")
            print(f"Warning: Using multiple choice prompt as fallback for type: {question_type}")
        
        return template.format(ocr_text=ocr_text, html_text=html_text)
    
    def get_answer_prompt(self, question_type: str, question_title: str, 
                         question_text: str, choices_text: str, language: str = "it") -> str:
        """
        Get prompt for answer generation.
        
        Args:
            question_type: Type of question
            question_title: Question title
            question_text: Question text
            choices_text: Formatted choices text
            language: Question language
            
        Returns:
            Formatted prompt for answer generation
        """
        template = self.prompts.get('answer_question', '')
        if not template:
            raise ConfigurationError("Answer generation prompt not found")
        
        return template.format(
            question_type=question_type,
            question_title=question_title,
            question_text=question_text,
            language=language,
            choices_text=choices_text
        )
    
    def get_prompt(self, prompt_key: str) -> Optional[str]:
        """
        Get a specific prompt by key.
        
        Args:
            prompt_key: Key of the prompt to retrieve
            
        Returns:
            Prompt template or None if not found
        """
        return self.prompts.get(prompt_key)
    
    def list_available_prompts(self) -> list[str]:
        """Get list of available prompt keys."""
        return list(self.prompts.keys())
    
    def reload_prompts(self) -> None:
        """Reload all prompt templates from files."""
        self.prompts.clear()
        self._load_prompts()
    
    def add_custom_prompt(self, key: str, template: str) -> None:
        """
        Add a custom prompt template.
        
        Args:
            key: Prompt key
            template: Prompt template string
        """
        self.prompts[key] = template
    
    def validate_prompts(self) -> Dict[str, bool]:
        """
        Validate that all required prompts are available.
        
        Returns:
            Dictionary mapping prompt keys to availability status
        """
        required_prompts = [
            'system_prompt',
            'extract_type',
            'extract_text_multiple_choice',
            'answer_question'
        ]
        
        validation_results = {}
        for prompt_key in required_prompts:
            validation_results[prompt_key] = prompt_key in self.prompts and bool(self.prompts[prompt_key])
        
        return validation_results