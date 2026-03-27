"""Google Gemini LLM provider implementation with vision support."""

import os
import threading
import time
from typing import Optional
from pathlib import Path
from .base import LLMProvider
from ..core.exceptions import ProcessingError


class GoogleProvider(LLMProvider):
    """Google Gemini LLM provider using LangChain."""

    # Class-level rate limiter: min seconds between requests (per model)
    _rate_locks: dict = {}
    _last_request_time: dict = {}
    _RATE_LIMIT_LOCK = threading.Lock()
    # 25 req/min = 2.4s interval; use 2.5s for safety margin
    MIN_REQUEST_INTERVAL = 2.5

    def __init__(self, model_name: str, api_key: Optional[str] = None,
                 temperature: float = 0.0, max_tokens: int = 2048):
        """
        Initialize Google provider.

        Args:
            model_name: Gemini model name
            api_key: API key (defaults to environment variable)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        super().__init__(model_name)
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._model = None
    
    def _initialize_model(self):
        """Initialize the LangChain model."""
        if self._model is None:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                from langchain.schema import HumanMessage
                
                # Model-specific configuration
                model_config = {
                    'model': self.model_name,
                    'temperature': self.temperature,
                    'google_api_key': self.api_key,
                }

                # Handle different model versions
                if 'gemini-2.5' in self.model_name:
                    # For Gemini 2.5 models, try without max_output_tokens first
                    try:
                        self._model = ChatGoogleGenerativeAI(**model_config)
                    except Exception:
                        model_config['max_output_tokens'] = self.max_tokens
                        self._model = ChatGoogleGenerativeAI(**model_config)
                else:
                    # For other models, use max_output_tokens
                    model_config['max_output_tokens'] = self.max_tokens
                    self._model = ChatGoogleGenerativeAI(**model_config)
                
                self._human_message = HumanMessage
            except ImportError as e:
                raise ProcessingError(f"Google Gemini dependencies not available: {e}")
    
    def query(self, prompt: str, system_prompt: str = None, image_path: Optional[str] = None, image_paths: Optional[list] = None):
        """
        Query Google Gemini model with a prompt and optional image(s).
        
        Args:
            prompt: Input prompt
            system_prompt: Optional system prompt to set context
            image_path: Optional path to single image file (for backward compatibility)
            image_paths: Optional list of paths to image files
            
        Returns:
            Tuple of (response_text, token_metadata) where token_metadata contains:
                - input_tokens: Number of prompt tokens
                - output_tokens: Number of completion tokens
            
        Raises:
            ProcessingError: If query fails
        """
        if not self.validate_prompt(prompt):
            raise ProcessingError("Invalid prompt provided")
        
        try:
            self._initialize_model()
            self._wait_for_rate_limit()

            # Determine which images to use
            images_to_process = []
            if image_paths:
                images_to_process = [img for img in image_paths if Path(img).exists()]
            elif image_path and Path(image_path).exists():
                images_to_process = [image_path]
            
            if images_to_process:
                # For vision queries, we need to use a different approach
                from langchain.schema import HumanMessage, SystemMessage
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
            
            # Extract token usage from response metadata
            token_metadata = {
                'input_tokens': 0,
                'output_tokens': 0
            }
            
            # Check for usage_metadata as a direct attribute (newer LangChain versions)
            # This is the primary location for token usage in recent Google Gemini API responses
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                
                # Extract tokens from usage_metadata
                # The response includes: input_tokens, output_tokens, total_tokens
                # and additional details like input_token_details (cache_read) and
                # output_token_details (reasoning tokens for models that support it)
                if isinstance(usage, dict):
                    token_metadata['input_tokens'] = usage.get('input_tokens', usage.get('prompt_token_count', 0))
                    token_metadata['output_tokens'] = usage.get('output_tokens', usage.get('candidates_token_count', 0))
                else:
                    # It might be an object with attributes
                    token_metadata['input_tokens'] = getattr(usage, 'input_tokens', getattr(usage, 'prompt_token_count', 0))
                    token_metadata['output_tokens'] = getattr(usage, 'output_tokens', getattr(usage, 'candidates_token_count', 0))
            
            # Also check response_metadata for backwards compatibility with older LangChain versions
            elif hasattr(response, 'response_metadata'):
                metadata = response.response_metadata
                
                # Google uses 'usage_metadata' field in response_metadata
                usage = metadata.get('usage_metadata', {})
                
                if usage:
                    token_metadata['input_tokens'] = usage.get('prompt_token_count', 0)
                    token_metadata['output_tokens'] = usage.get('candidates_token_count', 0)
            
            return response.content.strip(), token_metadata
        except Exception as e:
            raise ProcessingError(f"Google API error: {str(e)}")
    
    # Models with low rate limits (25 req/min)
    _RATE_LIMITED_MODELS = {"gemini-3.1-pro-preview", "gemini-3-pro-preview"}

    def _wait_for_rate_limit(self):
        """Enforce per-model rate limiting for quota-restricted models."""
        if self.model_name not in self._RATE_LIMITED_MODELS:
            return

        model_key = self.model_name
        with self._RATE_LIMIT_LOCK:
            if model_key not in self._rate_locks:
                self._rate_locks[model_key] = threading.Lock()
                self._last_request_time[model_key] = 0.0

        with self._rate_locks[model_key]:
            now = time.monotonic()
            elapsed = now - self._last_request_time[model_key]
            if elapsed < self.MIN_REQUEST_INTERVAL:
                time.sleep(self.MIN_REQUEST_INTERVAL - elapsed)
            self._last_request_time[model_key] = time.monotonic()

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 string."""
        import base64
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def get_model_name(self) -> str:
        """Get the full model name with provider prefix."""
        return f"google/{self.model_name}"
    
    def is_available(self) -> bool:
        """Check if Google provider is available."""
        if not self.api_key:
            return False
        
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return True
        except ImportError:
            return False
    
    def get_provider_info(self) -> dict:
        """Get detailed provider information."""
        info = super().get_provider_info()
        info.update({
            'provider_type': 'google',
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'has_api_key': bool(self.api_key)
        })
        return info