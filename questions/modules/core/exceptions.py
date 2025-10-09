"""Custom exceptions for the question processing pipeline."""

from typing import Dict, Any, Optional


class ProcessingError(Exception):
    """Base exception for processing errors."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context or {}
        self.message = message
    
    def __str__(self) -> str:
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} (Context: {context_str})"
        return self.message


class ConfigurationError(ProcessingError):
    """Exception raised for configuration issues."""
    pass


class OCRError(ProcessingError):
    """Exception raised during OCR processing."""
    pass


class VisionModelError(ProcessingError):
    """Exception raised during vision model processing."""
    pass


class SubmissionError(ProcessingError):
    """Exception raised during answer submission."""
    pass


class FileOperationError(ProcessingError):
    """Exception raised during file operations."""
    pass


class ValidationError(ProcessingError):
    """Exception raised during data validation."""
    pass


class ModelLoadError(ProcessingError):
    """Exception raised when models fail to load."""
    pass


class NetworkError(ProcessingError):
    """Exception raised for network-related issues."""
    pass


class BrowserAutomationError(ProcessingError):
    """Exception raised during browser automation."""
    pass