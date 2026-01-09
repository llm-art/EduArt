#!/usr/bin/env python3
"""
Gemini 2.5 Pro vision model implementation using LangChain
"""

import base64
from typing import Dict, Any, Optional
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from PIL import Image

from .base import VisionModel
from ..config import Config


class GeminiVisionModel(VisionModel):
    """Gemini 2.5 Pro vision model using LangChain"""
    
    def __init__(self, model_name: Optional[str] = None, **kwargs):
        """
        Initialize Gemini vision model
        
        Args:
            model_name: Gemini model name (defaults to config)
            **kwargs: Additional parameters
        """
        model_name = model_name or Config.GEMINI_MODEL_NAME
        super().__init__(model_name, **kwargs)
        
        self.llm = None
        self.api_key = Config.GOOGLE_API_KEY
        
        # Model configuration
        self.temperature = kwargs.get('temperature', Config.TEMPERATURE)
        self.max_tokens = kwargs.get('max_tokens', Config.MAX_NEW_TOKENS)
    
    def load_model(self) -> None:
        """Load the Gemini model via LangChain"""
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is required for Gemini model")
        
        try:
            print(f"Loading Gemini model: {self.model_name}")
            
            # Try with minimal configuration first
            self.llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=self.api_key,
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,  # Use max_output_tokens instead of max_tokens
                convert_system_message_to_human=True  # Gemini doesn't support system messages directly
            )
            
            self.is_loaded = True
            print(f"Successfully loaded Gemini model: {self.model_name}")
            
        except Exception as e:
            print(f"Error loading Gemini model: {e}")
            # Try fallback configuration
            try:
                print("Trying fallback configuration...")
                self.llm = ChatGoogleGenerativeAI(
                    model=self.model_name,
                    google_api_key=self.api_key,
                    convert_system_message_to_human=True
                )
                self.is_loaded = True
                print(f"Successfully loaded Gemini model with fallback config")
            except Exception as e2:
                print(f"Fallback also failed: {e2}")
                raise e
    
    def chat(self, image_path: str, system_prompt: str, user_prompt: str, max_tokens: Optional[int] = None) -> str:
        """
        Process image and text using Gemini via LangChain
        
        Args:
            image_path: Path to the image file
            system_prompt: System prompt for the model
            user_prompt: User prompt with instructions
            max_tokens: Optional maximum output tokens (overrides default)
            
        Returns:
            Generated text response
        """
        if not self.is_loaded:
            self.load_model()
        
        if not self.validate_image_path(image_path):
            raise ValueError(f"Invalid image path: {image_path}")
        
        try:
            if Config.VERBOSE:
                print(f"DEBUG: Starting Gemini chat with image: {image_path}")
                print(f"DEBUG: Model name: {self.model_name}")
                print(f"DEBUG: API key configured: {bool(self.api_key)}")
                if max_tokens:
                    print(f"DEBUG: Using custom max_tokens: {max_tokens}")
            
            # Create a new LLM instance with custom max_tokens if provided
            llm_to_use = self.llm
            if max_tokens is not None:
                llm_to_use = ChatGoogleGenerativeAI(
                    model=self.model_name,
                    google_api_key=self.api_key,
                    temperature=self.temperature,
                    max_output_tokens=max_tokens,
                    convert_system_message_to_human=True
                )
            
            # Read and encode image
            if Config.VERBOSE:
                print("DEBUG: Encoding image...")
            image_data = self._encode_image(image_path)
            if Config.VERBOSE:
                print(f"DEBUG: Image encoded, base64 length: {len(image_data)}")
            
            # Prepare messages - combine system and user prompts since Gemini doesn't support system messages
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            if Config.VERBOSE:
                print(f"DEBUG: Combined prompt length: {len(combined_prompt)}")
            
            # Try different content formats for better compatibility
            # Format 1: Standard multimodal format
            message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": combined_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{image_data}"
                    }
                ]
            )
            
            if Config.VERBOSE:
                print("DEBUG: Sending request to Gemini...")
            # Generate response
            response = llm_to_use.invoke([message])
            
            if Config.VERBOSE:
                print(f"DEBUG: Received response type: {type(response)}")
                print(f"DEBUG: Response object: {response}")
                print(f"DEBUG: Response has content attr: {hasattr(response, 'content')}")
            
            # Extract text from response
            result = response.content if hasattr(response, 'content') else str(response)
            
            if Config.VERBOSE:
                print(f"DEBUG: Extracted result type: {type(result)}")
                print(f"DEBUG: Result is None: {result is None}")
                print(f"DEBUG: Result length: {len(result) if result else 0}")
                print(f"DEBUG: Raw Gemini output: '{result[:200] if result else 'None'}...'")
            
            if not result:
                print("ERROR: Gemini returned empty/null response!")
                return ""
            
            return result
            
        except Exception as e:
            print(f"ERROR: Exception in Gemini chat: {e}")
            print(f"ERROR: Exception type: {type(e)}")
            import traceback
            print(f"ERROR: Traceback: {traceback.format_exc()}")
            raise
    
    def _encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 string
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string
        """
        try:
            # Open and convert image to RGB if needed
            with Image.open(image_path) as img:
                # Convert to RGB if not already
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save to bytes
                import io
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=95)
                img_byte_arr = img_byte_arr.getvalue()
                
                # Encode to base64
                return base64.b64encode(img_byte_arr).decode('utf-8')
                
        except Exception as e:
            print(f"Error encoding image {image_path}: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Gemini model is available"""
        return bool(self.api_key)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Gemini model information"""
        info = super().get_model_info()
        info.update({
            "provider": "Google",
            "model_type": "gemini",
            "api_key_configured": bool(self.api_key),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        })
        return info