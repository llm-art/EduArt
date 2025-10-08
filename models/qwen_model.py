#!/usr/bin/env python3
"""
Qwen2-VL vision model implementation using transformers with LangChain compatibility
"""

from typing import Dict, Any, Optional
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

from .base import VisionModel
from config import Config


class QwenVisionModel(VisionModel):
    """Qwen2-VL vision model with LangChain compatibility"""
    
    def __init__(self, model_name: Optional[str] = None, **kwargs):
        """
        Initialize Qwen vision model
        
        Args:
            model_name: Qwen model name/path (defaults to config)
            **kwargs: Additional parameters
        """
        model_name = model_name or Config.QWEN_MODEL_PATH
        super().__init__(model_name, **kwargs)
        
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Model configuration
        self.temperature = kwargs.get('temperature', Config.TEMPERATURE)
        self.max_tokens = kwargs.get('max_tokens', Config.MAX_NEW_TOKENS)
    
    def load_model(self) -> None:
        """Load the Qwen2-VL model and processor"""
        try:
            print(f"Loading Qwen2-VL model: {self.model_name}")
            
            # Load the model with proper configuration
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_name,
                dtype="auto",
                device_map="auto"
                # attn_implementation="flash_attention_2",  # Enable for better performance
            )
            
            self.processor = AutoProcessor.from_pretrained(self.model_name)
            
            self.is_loaded = True
            print(f"Successfully loaded Qwen2-VL model: {self.model_name}")
            
        except Exception as e:
            print(f"Error loading Qwen model: {e}")
            raise
    
    def chat(self, image_path: str, system_prompt: str, user_prompt: str) -> str:
        """
        Process image and text using Qwen2-VL
        
        Args:
            image_path: Path to the image file
            system_prompt: System prompt for the model
            user_prompt: User prompt with instructions
            
        Returns:
            Generated text response
        """
        if not self.is_loaded:
            self.load_model()
        
        if not self.validate_image_path(image_path):
            raise ValueError(f"Invalid image path: {image_path}")
        
        try:
            # Prepare messages with system prompt and user content
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image_path},
                        {"type": "text", "text": user_prompt}
                    ]
                }
            ]
            
            # Preparation for inference using the new API
            text = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            
            image_inputs, video_inputs = process_vision_info(messages)
            
            inputs = self.processor(
                text=[text], 
                images=image_inputs,
                videos=video_inputs,
                padding=True, 
                return_tensors="pt"
            )
            
            # Move to device if CUDA is available
            inputs = inputs.to(self.device)
            
            # Generate response with configured token limit
            generated_ids = self.model.generate(
                **inputs, 
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                do_sample=self.temperature > 0
            )
            
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            
            output_text = self.processor.batch_decode(
                generated_ids_trimmed, 
                skip_special_tokens=True, 
                clean_up_tokenization_spaces=False
            )
            
            # Fix: batch_decode returns a list, we need the first element as a string
            result = output_text[0] if output_text and len(output_text) > 0 else ""
            
            # Enhanced logging for debugging
            if Config.VERBOSE:
                print(f"DEBUG: Qwen model generated {len(generated_ids_trimmed[0]) if generated_ids_trimmed else 0} tokens")
                print(f"DEBUG: Raw Qwen output: '{result[:200]}...'")
            
            return result
            
        except Exception as e:
            print(f"Error in Qwen chat: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Qwen model is available"""
        try:
            # Check if we can import required dependencies
            import transformers
            from qwen_vl_utils import process_vision_info
            return True
        except ImportError:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Qwen model information"""
        info = super().get_model_info()
        info.update({
            "provider": "Qwen",
            "model_type": "qwen",
            "device": self.device,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "cuda_available": torch.cuda.is_available()
        })
        return info
    
    def __del__(self):
        """Cleanup model resources"""
        if hasattr(self, 'model') and self.model is not None:
            del self.model
        if hasattr(self, 'processor') and self.processor is not None:
            del self.processor
        
        # Clear CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()