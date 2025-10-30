"""Question parser for extracting question data from TXT files and creating prompts."""

import re
from typing import Dict, Any, List
from pathlib import Path
from ..core.exceptions import ProcessingError


class QuestionParser:
    """Parser for extracting question data from TXT files."""
    
    def __init__(self, question_mode: str = 'text'):
        """Initialize the parser and load the appropriate prompt template."""
        self.question_mode = question_mode
        self._load_prompt_template()
    
    def _load_prompt_template(self):
        """Load the appropriate prompt template from the prompts directory."""
        try:
            # Get the prompts directory relative to the questions directory
            current_dir = Path(__file__).parent.parent.parent.parent  # Go up to datasets root
            
            if self.question_mode == 'screenshot':
                prompt_file = current_dir / 'prompts' / 'answer_question_screenshot.txt'
            else:
                prompt_file = current_dir / 'prompts' / 'answer_question.txt'
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                self.prompt_template = f.read().strip()
        except Exception as e:
            raise ProcessingError(f"Failed to load prompt template: {e}")
    
    def parse_txt_file(self, filepath: str) -> Dict[str, Any]:
        """
        Parse TXT file and extract question components.
        
        Args:
            filepath: Path to the TXT file
            
        Returns:
            Dictionary with question components
            
        Raises:
            ProcessingError: If file cannot be read or parsed
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
        except Exception as e:
            raise ProcessingError(f"Error reading file {filepath}: {e}")
        
        lines = content.split('\n')
        
        # Extract components
        title = ""
        question_type = ""
        instructions = ""
        question_text = ""
        choices = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith("Title:"):
                title = line[6:].strip()
            elif line in ["SCELTA MULTIPLA", "VERO O FALSO", "COMPLETAMENTO APERTO", 
                         "POSIZIONAMENTO", "COMPLETAMENTO CHIUSO", "TROVA ERRORE"]:
                question_type = self._map_question_type(line)
                # Get instructions (next line)
                if i + 1 < len(lines):
                    instructions = lines[i + 1].strip()
                    i += 1
            elif line.startswith("Question:"):
                question_text = line[9:].strip()
                # Continue reading question text until we hit "Choices:" or end
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith("Choices:"):
                    if lines[j].strip():
                        question_text += " " + lines[j].strip()
                    j += 1
                i = j - 1
            elif line.startswith("Choices:"):
                # Read all choices
                j = i + 1
                while j < len(lines):
                    choice_line = lines[j].strip()
                    if choice_line:
                        choices.append(choice_line)
                    j += 1
                break
            
            i += 1
        
        return {
            'title': title,
            'question_type': question_type,
            'instructions': instructions,
            'question_text': question_text,
            'choices': choices
        }
    
    def _map_question_type(self, italian_type: str) -> str:
        """Map Italian question type to internal type."""
        mapping = {
            "SCELTA MULTIPLA": "multiple_choice_radio",  # Will be refined based on instructions
            "VERO O FALSO": "true_false",
            "COMPLETAMENTO APERTO": "completion_open",
            "POSIZIONAMENTO": "positioning",
            "COMPLETAMENTO CHIUSO": "completion_closed",
            "TROVA ERRORE": "select_errors"
        }
        return mapping.get(italian_type, "unknown")
    
    def refine_question_type(self, question_data: Dict[str, Any]) -> str:
        """
        Refine question type based on instructions and choices.
        
        Args:
            question_data: Question data dictionary
            
        Returns:
            Refined question type
        """
        base_type = question_data['question_type']
        instructions = question_data['instructions'].lower()
        
        if base_type == "multiple_choice_radio":
            if "tutte le risposte" in instructions or "scegli tutte" in instructions:
                return "multiple_choice_check"
            elif len(question_data['choices']) <= 4:
                return "multiple_choice"
        
        return base_type
    
    def _format_choices_for_english_template(self, choices: List[str]) -> str:
        """
        Format choices for the English template system.
        
        Args:
            choices: List of choice strings
            
        Returns:
            Formatted choices text
        """
        if not choices:
            return ""
        
        choices_text = "Options:\n\n"
        for choice in choices:
            choices_text += f"{choice}\n\n"
        
        return choices_text.strip()
    
    def _map_question_type_to_english(self, question_type: str) -> str:
        """
        Map internal question type to English template format.
        
        Args:
            question_type: Internal question type
            
        Returns:
            English question type for template
        """
        mapping = {
            "multiple_choice_radio": "multiple choice radio",
            "multiple_choice": "multiple choice radio",
            "multiple_choice_check": "multiple choice check",
            "true_false": "true/false",
            "completion_open": "open completion",
            "completion_closed": "closed completion",
            "positioning": "positioning",
            "select_errors": "error selection"
        }
        return mapping.get(question_type, "multiple choice radio")
    
    def create_prompt(self, question_data: Dict[str, Any]) -> str:
        """
        Create complete prompt for LLM using the appropriate template system.
        
        Args:
            question_data: Question data dictionary
            
        Returns:
            Complete LLM prompt
        """
        if self.question_mode == 'screenshot':
            # For screenshot mode, use the simple screenshot prompt
            return self.prompt_template
        else:
            # For text mode, use the original template formatting
            question_type = self.refine_question_type(question_data)
            
            # Format choices for the English template
            choices_text = self._format_choices_for_english_template(question_data.get('choices', []))
            
            # Generate type-specific instructions
            instructions = self._get_type_specific_instructions(question_type)
            
            # Use the loaded English template and format it
            prompt = self.prompt_template.format(
                question_text=question_data.get('question_text', ''),
                choices_text=choices_text,
                instructions=instructions
            )
            
            return prompt
    
    def _get_type_specific_instructions(self, question_type: str) -> str:
        """
        Generate type-specific instructions for the LLM.
        
        Args:
            question_type: Internal question type
            
        Returns:
            Type-specific instruction text
        """
        instructions_map = {
            "multiple_choice_radio": "Respond with the correct statement, ONLY the letter (e.g., A, B, C, or D)",
            "multiple_choice": "Respond with the correct statement, ONLY the letter (e.g., A, B, C, or D)",
            "multiple_choice_check": "Respond with the correct statements, ONLY the letters (e.g., \"A; B; C\")",
            "true_false": "Respond with true or false for each statement (e.g., \"A: true, B: false\")",
            "completion_open": "Provide a concise answer",
            "completion_closed": "Provide answers for ALL blanks in the format \"BLANK_1: full text answer, BLANK_2: full text answer\" (continue for all blanks present). Use the COMPLETE TEXT of your chosen option, NOT numbers",
            "positioning": "Provide the correct sequence or position",
            "select_errors": "Identify the errors"
        }
        
        return instructions_map.get(question_type, "Provide the best answer based on the question type")
    
    def get_question_id_from_path(self, txt_file: str) -> str:
        """
        Extract question ID from filename.
        
        Args:
            txt_file: Path to TXT file
            
        Returns:
            Question ID
        """
        filename = Path(txt_file).name
        return filename[:4] if filename.endswith('.txt') and len(filename) == 8 else filename
    
    def validate_question_data(self, question_data: Dict[str, Any]) -> bool:
        """
        Validate question data completeness.
        
        Args:
            question_data: Question data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['question_type', 'question_text']
        return all(question_data.get(field) for field in required_fields)
    
    def find_screenshot_files(self) -> List[str]:
        """
        Find all PNG screenshot files in dataset/raw directory.
        
        Returns:
            List of PNG file paths
        """
        try:
            # Get the dataset/raw directory
            current_dir = Path(__file__).parent.parent.parent.parent  # Go up to datasets root
            raw_dir = current_dir / 'dataset' / 'raw'
            
            if not raw_dir.exists():
                return []
            
            # Find all PNG files
            png_files = list(raw_dir.glob('*.png'))
            return [str(f) for f in sorted(png_files)]
        except Exception as e:
            raise ProcessingError(f"Error finding screenshot files: {e}")
    
    def parse_screenshot_file(self, png_file: str) -> Dict[str, Any]:
        """
        Create minimal question data for screenshot mode.
        
        Args:
            png_file: Path to PNG screenshot file
            
        Returns:
            Dictionary with minimal question components for screenshot mode
        """
        filename = Path(png_file).stem
        
        # Look for additional images in dataset/imgs with same filename
        additional_images = self._find_additional_images(filename)
        
        return {
            'title': f"Screenshot Question {filename}",
            'question_type': 'screenshot',  # Will be determined from metadata
            'instructions': 'Read the question in the image and answer it',
            'question_text': f'Question from screenshot {filename}',
            'choices': [],
            'screenshot_file': png_file,
            'additional_images': additional_images
        }
    
    def _find_additional_images(self, filename: str) -> List[str]:
        """
        Find additional images in dataset/imgs with the same filename.
        
        Args:
            filename: Base filename (without extension)
            
        Returns:
            List of additional image paths
        """
        try:
            # Get the dataset/imgs directory
            current_dir = Path(__file__).parent.parent.parent.parent  # Go up to datasets root
            imgs_dir = current_dir / 'dataset' / 'imgs'
            
            if not imgs_dir.exists():
                return []
            
            # Convert filename to 4-digit format (e.g., "1" -> "0001")
            padded_filename = filename.zfill(4)
            
            # Look for images with same base name but different extensions
            additional_images = []
            for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                img_path = imgs_dir / f"{padded_filename}{ext}"
                if img_path.exists():
                    additional_images.append(str(img_path))
            
            return additional_images
        except Exception as e:
            print(f"Warning: Error finding additional images for {filename}: {e}")
            return []