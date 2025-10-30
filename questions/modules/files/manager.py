"""
File and directory management utilities.

This module handles file operations, directory creation, and path management.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class FileManager:
    """Manages file operations and directory structure."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize FileManager.
        
        Args:
            base_dir: Base directory for file operations. Defaults to script directory.
        """
        if base_dir is None:
            self.base_dir = Path(__file__).parent.parent.parent.resolve()
        else:
            self.base_dir = Path(base_dir).resolve()
        
        self.data_dir = self.base_dir / "data"
    
    def create_exercise_directories(self, exercise_number: int) -> Dict[str, Path]:
        """
        Create directory structure for an exercise.
        
        Args:
            exercise_number: Exercise number
            
        Returns:
            Dictionary with directory paths
        """
        exercise_dir = self.data_dir / str(exercise_number)
        imgs_dir = exercise_dir / "imgs"
        raw_dir = exercise_dir / "raw"
        
        # Create directories
        imgs_dir.mkdir(parents=True, exist_ok=True)
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"✓ Created directories for exercise {exercise_number}")
        
        return {
            'exercise': exercise_dir,
            'imgs': imgs_dir,
            'raw': raw_dir
        }
    
    def get_exercise_directories(self, exercise_number: int) -> Dict[str, Path]:
        """
        Get directory paths for an exercise.
        
        Args:
            exercise_number: Exercise number
            
        Returns:
            Dictionary with directory paths
        """
        exercise_dir = self.data_dir / str(exercise_number)
        imgs_dir = exercise_dir / "imgs"
        raw_dir = exercise_dir / "raw"
        
        return {
            'exercise': exercise_dir,
            'imgs': imgs_dir,
            'raw': raw_dir
        }
    
    def save_html_content(
        self, 
        content: str, 
        question_number: int, 
        exercise_number: int,
        title: str = None
    ) -> Path:
        """
        Save HTML content to a file.
        
        Args:
            content: HTML content to save
            question_number: Question number
            exercise_number: Exercise number
            title: Optional title for the question
            
        Returns:
            Path to the saved file
        """
        dirs = self.create_exercise_directories(exercise_number)
        html_file = dirs['raw'] / f"{question_number}.html"
        
        # Create full HTML document
        html_document = self._create_html_document(content, question_number, title)
        
        try:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_document)
            print(f"✓ HTML content saved: {html_file.name}")
            return html_file
        except Exception as e:
            print(f"❌ Error saving HTML content: {e}")
            raise
    
    def _create_html_document(self, content: str, question_number: int, title: str = None) -> str:
        """
        Create a complete HTML document from content.
        
        Args:
            content: HTML content
            question_number: Question number
            title: Optional title
            
        Returns:
            Complete HTML document string
        """
        page_title = title or f"Question {question_number}"
        
        return f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            line-height: 1.6;
        }}
        .question-header {{ 
            border-bottom: 2px solid #ccc; 
            padding-bottom: 10px; 
            margin-bottom: 20px; 
        }}
        .question-content {{ 
            line-height: 1.6; 
        }}
        img {{ 
            max-width: 100%; 
            height: auto; 
            margin: 10px 0; 
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .metadata {{
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 20px;
            font-size: 0.9em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="metadata">
        <strong>Question {question_number}</strong><br>
        Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
        Source: Zanichelli Exercise Automation
    </div>
    <div class="question-header">
        <h1>{page_title}</h1>
    </div>
    <div class="question-content">
        {content}
    </div>
</body>
</html>"""
    
    def get_screenshot_path(self, question_number: int, exercise_number: int) -> Path:
        """
        Get the path for a question screenshot.
        
        Args:
            question_number: Question number
            exercise_number: Exercise number
            
        Returns:
            Path for the screenshot
        """
        dirs = self.get_exercise_directories(exercise_number)
        return dirs['raw'] / f"{question_number}.png"
    
    def get_pre_screenshot_path(self, question_number: int, exercise_number: int) -> Path:
        """
        Get the path for a pre-interaction question screenshot.
        
        Args:
            question_number: Question number
            exercise_number: Exercise number
            
        Returns:
            Path for the pre-interaction screenshot
        """
        dirs = self.get_exercise_directories(exercise_number)
        return dirs['raw'] / f"pre_{question_number}.png"
    
    def get_image_path(
        self, 
        question_number: int, 
        exercise_number: int, 
        extension: str = "jpg",
        index: int = 0
    ) -> Path:
        """
        Get the path for a question image.
        
        Args:
            question_number: Question number
            exercise_number: Exercise number
            extension: File extension
            index: Image index (for multiple images per question)
            
        Returns:
            Path for the image
        """
        dirs = self.get_exercise_directories(exercise_number)
        
        if index == 0:
            filename = f"{question_number}.{extension}"
        else:
            filename = f"{question_number}_{index + 1}.{extension}"
        
        return dirs['imgs'] / filename
    
    def clean_filename(self, filename: str, max_length: int = 100) -> str:
        """
        Clean a filename by removing invalid characters.
        
        Args:
            filename: Original filename
            max_length: Maximum filename length
            
        Returns:
            Cleaned filename
        """
        # Remove invalid characters for directory/file names
        invalid_chars = ['/', '\\', ':', '<', '>', '|', '?', '*', '"']
        clean_name = filename
        
        for char in invalid_chars:
            clean_name = clean_name.replace(char, '_')
        
        # Replace spaces with underscores and convert to lowercase
        clean_name = clean_name.replace(' ', '_').lower()
        
        # Limit length
        if len(clean_name) > max_length:
            clean_name = clean_name[:max_length]
        
        return clean_name
    
    def list_exercise_files(self, exercise_number: int) -> Dict[str, List[Path]]:
        """
        List all files for an exercise.
        
        Args:
            exercise_number: Exercise number
            
        Returns:
            Dictionary with file lists by type
        """
        dirs = self.get_exercise_directories(exercise_number)
        
        result = {
            'screenshots': [],
            'images': [],
            'html': []
        }
        
        # List screenshots (PNG files in raw/)
        if dirs['raw'].exists():
            result['screenshots'] = list(dirs['raw'].glob('*.png'))
        
        # List images (various formats in imgs/)
        if dirs['imgs'].exists():
            image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp']
            for ext in image_extensions:
                result['images'].extend(dirs['imgs'].glob(ext))
        
        # List HTML files (in raw/)
        if dirs['raw'].exists():
            result['html'] = list(dirs['raw'].glob('*.html'))
        
        return result
    
    def get_exercise_summary(self, exercise_number: int) -> Dict[str, Any]:
        """
        Get a summary of files for an exercise.
        
        Args:
            exercise_number: Exercise number
            
        Returns:
            Summary dictionary
        """
        files = self.list_exercise_files(exercise_number)
        dirs = self.get_exercise_directories(exercise_number)
        
        return {
            'exercise_number': exercise_number,
            'directories': {
                'exercise': str(dirs['exercise']),
                'imgs': str(dirs['imgs']),
                'raw': str(dirs['raw'])
            },
            'file_counts': {
                'screenshots': len(files['screenshots']),
                'images': len(files['images']),
                'html': len(files['html'])
            },
            'files': files
        }
    
    def ensure_directory_exists(self, directory: Path) -> None:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            directory: Directory path
        """
        directory.mkdir(parents=True, exist_ok=True)
    
    def get_base_dir(self) -> Path:
        """Get the base directory."""
        return self.base_dir
    
    def get_data_dir(self) -> Path:
        """Get the data directory."""
        return self.data_dir