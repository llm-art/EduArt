"""HTML service for text extraction from HTML files."""

import re
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup

from ..core.exceptions import FileOperationError


class HTMLService:
    """Service for extracting text content from HTML files."""
    
    def __init__(self):
        """Initialize HTML service."""
        pass
    
    def extract_text(self, html_path: Path) -> str:
        """
        Extract clean text from HTML file.
        
        Args:
            html_path: Path to the HTML file
            
        Returns:
            Extracted text as string
            
        Raises:
            FileOperationError: If file operations fail
        """
        if not html_path.exists():
            raise FileOperationError(f"HTML file not found: {html_path}")
        
        try:
            print(f"Extracting text from HTML: {html_path}")
            
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text from the question content div
            question_content = soup.find('div', class_='question-content')
            if question_content:
                # Get text and clean it up
                text = question_content.get_text()
            else:
                # Fallback: get all text from body
                body = soup.find('body')
                if body:
                    text = body.get_text()
                else:
                    text = soup.get_text()
            
            # Clean up the text
            text = self._clean_text(text)
            
            print(f"HTML extracted {len(text)} characters")
            return text
            
        except Exception as e:
            raise FileOperationError(f"HTML text extraction failed for {html_path}: {e}")
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing extra whitespace and formatting.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove common HTML artifacts
        text = re.sub(r'Come si fa\?.*?Leggi come fare nelle Faq\.', '', text, flags=re.DOTALL)
        text = re.sub(r'Generated on:.*?Source:.*?Automation', '', text, flags=re.DOTALL)
        text = re.sub(r'Question \d+', '', text)
        
        # Clean up remaining artifacts
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def is_available(self) -> bool:
        """Check if HTML service is available."""
        try:
            # Test if BeautifulSoup is available
            BeautifulSoup("<html></html>", 'html.parser')
            return True
        except Exception:
            return False