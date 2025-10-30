"""Anthropic Claude LLM provider implementation."""

import os
from typing import Optional
from .base import LLMProvider
from ..core.exceptions import ProcessingError


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider using LangChain."""
    
    def __init__(self, model_name: str, api_key: Optional[str] = None, 
                 temperature: float = 0.1, max_tokens: int = 512, timeout: int = 30):
        """
        Initialize Anthropic provider.
        
        Args:
            model_name: Claude model name
            api_key: API key (defaults to environment variable)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
        """
        super().__init__(model_name)
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._model = None
    
    def _initialize_model(self):
        """Initialize the LangChain model."""
        if self._model is None:
            try:
                from langchain_anthropic import ChatAnthropic
                from langchain.schema import HumanMessage
                
                self._model = ChatAnthropic(
                    model=self.model_name,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    timeout=self.timeout,
                    anthropic_api_key=self.api_key
                )
                self._human_message = HumanMessage
            except ImportError as e:
                raise ProcessingError(f"Anthropic dependencies not available: {e}")
    
    def query(self, prompt: str, image_path: Optional[str] = None, image_paths: Optional[list] = None) -> str:
        """
        Query Anthropic Claude model with a prompt and optional image(s).
        
        Args:
            prompt: Input prompt
            image_path: Optional path to single image file (not supported yet)
            image_paths: Optional list of paths to image files (not supported yet)
            
        Returns:
            Model response
            
        Raises:
            ProcessingError: If query fails
        """
        if not self.validate_prompt(prompt):
            raise ProcessingError("Invalid prompt provided")
        
        if image_path or image_paths:
            raise ProcessingError("Image support not implemented for Anthropic provider yet")
        
        try:
            self._initialize_model()
            response = self._model.invoke([self._human_message(content=prompt)])
            return response.content.strip()
        except Exception as e:
            raise ProcessingError(f"Anthropic API error: {str(e)}")
    
    def get_model_name(self) -> str:
        """Get the full model name with provider prefix."""
        return f"anthropic/{self.model_name}"
    
    def is_available(self) -> bool:
        """Check if Anthropic provider is available."""
        if not self.api_key:
            return False
        
        try:
            from langchain_anthropic import ChatAnthropic
            return True
        except ImportError:
            return False
    
    def get_provider_info(self) -> dict:
        """Get detailed provider information."""
        info = super().get_provider_info()
        info.update({
            'provider_type': 'anthropic',
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'timeout': self.timeout,
            'has_api_key': bool(self.api_key)
        })
        return info