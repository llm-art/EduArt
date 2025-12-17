"""Configuration for the LLM questioner."""

import os
import glob
from pathlib import Path
from typing import List, Optional
from ..core.exceptions import ConfigurationError


class QuestionerConfig:
    """Configuration for the LLM questioner."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize configuration with environment variables.
        
        Args:
            base_dir: Base directory for dataset operations (defaults to project root)
        """
        # Determine base directory
        if base_dir is None:
            # Default to project root (datasets directory)
            questions_dir = Path(__file__).parent.parent.parent.parent
            base_dir = questions_dir
        else:
            base_dir = Path(base_dir)
        
        # Dataset paths relative to base directory
        self.dataset_dir = base_dir / 'dataset' / 'data'
        self.results_dir = base_dir / 'results'
        
        # Ensure directories exist
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def find_question_files(self, start: Optional[int] = None, end: Optional[int] = None, 
                           question_types: Optional[List[str]] = None) -> List[str]:
        """
        Find question TXT files in the dataset directory.
        
        Args:
            start: Start question number
            end: End question number
            question_types: List of question types to filter by
            
        Returns:
            List of question file paths
        """
        pattern = str(self.dataset_dir / "*.txt")
        txt_files = sorted(glob.glob(pattern))
        
        # Filter by range if specified
        if start is not None or end is not None:
            filtered_files = []
            for txt_file in txt_files:
                filename = Path(txt_file).name
                if filename.endswith('.txt') and len(filename) == 8:  # XXXX.txt
                    try:
                        file_num = int(filename[:4])
                        if (start is None or file_num >= start) and (end is None or file_num <= end):
                            filtered_files.append(txt_file)
                    except ValueError:
                        continue
            txt_files = filtered_files
        
        # Filter by question types if specified
        if question_types:
            from ..processors.question_parser import QuestionParser
            parser = QuestionParser()
            filtered_files = []
            for txt_file in txt_files:
                try:
                    question_data = parser.parse_txt_file(txt_file)
                    refined_type = parser.refine_question_type(question_data)
                    if refined_type in question_types:
                        filtered_files.append(txt_file)
                except Exception as e:
                    print(f"Warning: Error parsing {txt_file} for type filtering: {e}")
            txt_files = filtered_files
        
        return txt_files
    
    def validate_dataset_directory(self) -> bool:
        """
        Validate that the dataset directory exists and contains files.
        
        Returns:
            True if valid, False otherwise
        """
        if not self.dataset_dir.exists():
            return False

        
        txt_files = list(self.dataset_dir.glob("*.txt"))
        return len(txt_files) > 0
    
    def get_question_metadata_path(self, txt_file: str) -> str:
        """
        Get the corresponding JSON metadata file path for a TXT file.
        
        Args:
            txt_file: Path to TXT file
            
        Returns:
            Path to corresponding JSON file
        """
        return txt_file.replace('data/', 'metadata/').replace('.txt', '.json')
    
    def validate_configuration(self) -> List[str]:
        """
        Validate the configuration and return any issues.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        if not self.validate_dataset_directory():
            errors.append(f"Dataset directory not found or empty: {self.dataset_dir}")
        
        # Check for required environment variables
        required_env_vars = ['GOOGLE_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY']
        available_keys = [var for var in required_env_vars if os.getenv(var)]
        
        if not available_keys:
            errors.append("No API keys found. At least one of GOOGLE_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY is required.")
        
        return errors
    
    def print_configuration_status(self):
        """Print current configuration status."""
        print("=== LLM Questioner Configuration ===")
        print(f"Dataset Directory: {self.dataset_dir}")
        print(f"Results Directory: {self.results_dir}")
        print(f"Dataset Valid: {self.validate_dataset_directory()}")
        
        # Check API keys
        api_keys = {
            'OpenAI': bool(os.getenv('OPENAI_API_KEY')),
            'Google': bool(os.getenv('GOOGLE_API_KEY')),
            'Anthropic': bool(os.getenv('ANTHROPIC_API_KEY'))
        }
        
        print("API Keys:")
        for provider, available in api_keys.items():
            status = "✓" if available else "✗"
            print(f"  {provider}: {status}")
        
        # Count available questions
        if self.validate_dataset_directory():
            question_files = self.find_question_files()
            print(f"Available Questions: {len(question_files)}")
        
        print("=" * 40)