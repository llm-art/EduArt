"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, model_name: str, **kwargs):
        """
        Initialize LLM provider.
        
        Args:
            model_name: Name of the model
            **kwargs: Additional provider-specific parameters
        """
        self.model_name = model_name
        self.config = kwargs
    
    @abstractmethod
    def query(self, prompt: str, image_path: Optional[str] = None, image_paths: Optional[list] = None) -> str:
        """
        Query the LLM with a prompt and optional image(s), return the response.
        
        Args:
            prompt: The input prompt
            image_path: Optional path to single image file for vision models (for backward compatibility)
            image_paths: Optional list of paths to image files for vision models
            
        Returns:
            The LLM response
            
        Raises:
            Exception: If the query fails
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the full model name identifier.
        
        Returns:
            Model name with provider prefix
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is available and properly configured.
        
        Returns:
            True if available, False otherwise
        """
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the provider.
        
        Returns:
            Dictionary with provider information
        """
        return {
            'model_name': self.model_name,
            'provider': self.__class__.__name__,
            'config': self.config,
            'available': self.is_available()
        }
    
    def validate_prompt(self, prompt: str) -> bool:
        """
        Validate that the prompt is suitable for this provider.
        
        Args:
            prompt: The prompt to validate
            
        Returns:
            True if valid, False otherwise
        """
        return isinstance(prompt, str) and len(prompt.strip()) > 0
    
    def __str__(self) -> str:
        """String representation of the provider."""
        return f"{self.__class__.__name__}({self.model_name})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the provider."""
        return f"{self.__class__.__name__}(model_name='{self.model_name}', config={self.config})"