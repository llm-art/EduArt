"""Anthropic Claude LLM provider implementation with vision support."""

import os
from typing import Optional
from pathlib import Path
from .base import LLMProvider
from ..core.exceptions import ProcessingError


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider using LangChain with vision support."""
    
    def __init__(self, model_name: str, api_key: Optional[str] = None,
                 temperature: float = 0.0, max_tokens: int = 512, timeout: int = 30):
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
    
    def query(self, prompt: str, system_prompt: str = None, image_path: Optional[str] = None, image_paths: Optional[list] = None) -> str:
        """
        Query Anthropic Claude model with a prompt and optional image(s).
        
        Args:
            prompt: Input prompt
            system_prompt: Optional system prompt to set context
            image_path: Optional path to single image file
            image_paths: Optional list of paths to image files
            
        Returns:
            Model response
            
        Raises:
            ProcessingError: If query fails
        """
        if not self.validate_prompt(prompt):
            raise ProcessingError("Invalid prompt provided")
        
        try:
            self._initialize_model()
            
            # Determine which images to use
            images_to_process = []
            if image_paths:
                images_to_process = [img for img in image_paths if Path(img).exists()]
            elif image_path and Path(image_path).exists():
                images_to_process = [image_path]
            
            if images_to_process:
                # For vision queries with images
                from langchain_core.messages import HumanMessage, SystemMessage
                
                # Combine system prompt with user prompt if provided
                full_prompt = prompt
                if system_prompt:
                    full_prompt = f"{system_prompt}\n\n{prompt}"
                
                # Create message with text and images
                message_content = [{"type": "text", "text": full_prompt}]
                
                # Add all images to the message
                for img_path in images_to_process:
                    # Determine image type from extension
                    img_ext = Path(img_path).suffix.lower()
                    if img_ext in ['.jpg', '.jpeg']:
                        img_type = 'image/jpeg'
                    elif img_ext == '.png':
                        img_type = 'image/png'
                    elif img_ext == '.gif':
                        img_type = 'image/gif'
                    elif img_ext == '.webp':
                        img_type = 'image/webp'
                    else:
                        img_type = 'image/png'  # Default
                    
                    message_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{img_type};base64,{self._encode_image(img_path)}"
                        }
                    })
                
                message = HumanMessage(content=message_content)
                response = self._model.invoke([message])
            else:
                # Text-only query
                messages = []
                if system_prompt:
                    from langchain_core.messages import SystemMessage
                    messages.append(SystemMessage(content=system_prompt))
                messages.append(self._human_message(content=prompt))
                response = self._model.invoke(messages)
            
            return response.content.strip()
        except Exception as e:
            raise ProcessingError(f"Anthropic API error: {str(e)}")
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 string."""
        import base64
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
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