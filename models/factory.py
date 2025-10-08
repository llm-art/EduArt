#!/usr/bin/env python3
"""
Factory for creating vision models based on configuration
"""

from typing import Optional
from .base import VisionModel
from .qwen_model import QwenVisionModel
from .gemini_model import GeminiVisionModel
from config import Config


def create_vision_model(model_type: Optional[str] = None, **kwargs) -> VisionModel:
    """
    Create a vision model based on configuration
    
    Args:
        model_type: Override model type ("qwen" or "gemini")
        **kwargs: Additional model parameters
        
    Returns:
        VisionModel instance
        
    Raises:
        ValueError: If model type is invalid or model is not available
    """
    # Use provided model type or fall back to config
    model_type = (model_type or Config.MODEL_TYPE).lower()
    
    print(f"Instantiating vision model: {model_type}")
    
    if model_type == "qwen":
        model = QwenVisionModel(**kwargs)
        if not model.is_available():
            raise ValueError("Qwen model dependencies are not available. Please install transformers and qwen-vl-utils.")
        return model
    
    elif model_type == "gemini":
        model = GeminiVisionModel(**kwargs)
        if not model.is_available():
            raise ValueError("Gemini model is not available. Please set GOOGLE_API_KEY environment variable.")
        return model
    
    else:
        raise ValueError(f"Unsupported model type: {model_type}. Supported types: 'qwen', 'gemini'")


def get_available_models() -> dict:
    """
    Get information about available models
    
    Returns:
        Dictionary with model availability information
    """
    models_info = {}
    
    # Check Qwen availability
    try:
        qwen_model = QwenVisionModel()
        models_info["qwen"] = {
            "available": qwen_model.is_available(),
            "info": qwen_model.get_model_info()
        }
    except Exception as e:
        models_info["qwen"] = {
            "available": False,
            "error": str(e)
        }
    
    # Check Gemini availability
    try:
        gemini_model = GeminiVisionModel()
        models_info["gemini"] = {
            "available": gemini_model.is_available(),
            "info": gemini_model.get_model_info()
        }
    except Exception as e:
        models_info["gemini"] = {
            "available": False,
            "error": str(e)
        }
    
    return models_info


def validate_model_config() -> bool:
    """
    Validate that the configured model is available
    
    Returns:
        True if configured model is available, False otherwise
    """
    try:
        model = create_vision_model()
        return model.is_available()
    except Exception as e:
        print(f"Model validation failed: {e}")
        return False


def print_model_status():
    """Print status of all available models"""
    print("\n=== Vision Models Status ===")
    
    models_info = get_available_models()
    
    for model_name, info in models_info.items():
        status = "✓ Available" if info["available"] else "✗ Not Available"
        print(f"{model_name.upper()}: {status}")
        
        if not info["available"] and "error" in info:
            print(f"  Error: {info['error']}")
        elif info["available"] and "info" in info:
            model_info = info["info"]
            print(f"  Model: {model_info.get('model_name', 'Unknown')}")
            if "provider" in model_info:
                print(f"  Provider: {model_info['provider']}")
    
    print(f"\nConfigured model: {Config.MODEL_TYPE.upper()}")
    print(f"Configuration valid: {'✓' if validate_model_config() else '✗'}")
    print("=" * 30)