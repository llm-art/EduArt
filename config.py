#!/usr/bin/env python3
"""
Configuration module for exam question processor
Handles environment variables and model settings
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the exam question processor"""
    
    # Model Configuration
    MODEL_TYPE: str = os.getenv("MODEL_TYPE", "qwen").lower()
    
    # Google Gemini Configuration
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro")
    
    # Qwen Configuration
    QWEN_MODEL_PATH: str = os.getenv("QWEN_MODEL_PATH", "Qwen/Qwen2-VL-7B-Instruct")
    
    # Processing Configuration
    MAX_NEW_TOKENS: int = int(os.getenv("MAX_NEW_TOKENS", "512"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))
    
    # OCR Configuration
    OCR_LANG: str = os.getenv("OCR_LANG", "it")
    TEXT_DETECTION_MODEL: str = os.getenv("TEXT_DETECTION_MODEL", "PP-OCRv5_mobile_det")
    TEXT_RECOGNITION_MODEL: str = os.getenv("TEXT_RECOGNITION_MODEL", "PP-OCRv5_mobile_rec")
    
    # Debug Configuration
    VERBOSE: bool = False  # Will be set dynamically by CLI
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration settings"""
        if cls.MODEL_TYPE not in ["qwen", "gemini"]:
            raise ValueError(f"Invalid MODEL_TYPE: {cls.MODEL_TYPE}. Must be 'qwen' or 'gemini'")
        
        if cls.MODEL_TYPE == "gemini" and not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is required when MODEL_TYPE is 'gemini'")
        
        if cls.MAX_NEW_TOKENS <= 0:
            raise ValueError("MAX_NEW_TOKENS must be positive")
        
        if not 0 <= cls.TEMPERATURE <= 2:
            raise ValueError("TEMPERATURE must be between 0 and 2")
    
    @classmethod
    def get_model_info(cls) -> dict:
        """Get current model configuration info"""
        return {
            "model_type": cls.MODEL_TYPE,
            "model_name": cls.GEMINI_MODEL_NAME if cls.MODEL_TYPE == "gemini" else cls.QWEN_MODEL_PATH,
            "max_tokens": cls.MAX_NEW_TOKENS,
            "temperature": cls.TEMPERATURE
        }

# Validate configuration on import
Config.validate()