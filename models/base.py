#!/usr/bin/env python3
"""
Abstract base class for vision models
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path


class VisionModel(ABC):
    """Abstract base class for vision models that can process images and text"""
    
    def __init__(self, model_name: str, **kwargs):
        """
        Initialize the vision model
        
        Args:
            model_name: Name/path of the model
            **kwargs: Additional model-specific parameters
        """
        self.model_name = model_name
        self.is_loaded = False
        self.config = kwargs
    
    @abstractmethod
    def load_model(self) -> None:
        """Load the model and processor"""
        pass
    
    @abstractmethod
    def chat(self, image_path: str, system_prompt: str, user_prompt: str) -> str:
        """
        Process image and text to generate a response
        
        Args:
            image_path: Path to the image file
            system_prompt: System prompt for the model
            user_prompt: User prompt with instructions
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the model is available and properly configured"""
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model"""
        return {
            "model_name": self.model_name,
            "is_loaded": self.is_loaded,
            "config": self.config
        }
    
    def validate_image_path(self, image_path: str) -> bool:
        """Validate that the image path exists and is readable"""
        try:
            path = Path(image_path)
            return path.exists() and path.is_file()
        except Exception:
            return False
    
    def __enter__(self):
        """Context manager entry"""
        if not self.is_loaded:
            self.load_model()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        # Cleanup if needed
        pass