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
    
    # ========================================================================
    # Question Preprocessing Configuration (Scripts 1-3)
    # ========================================================================
    
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
    
    # ========================================================================
    # LLM Evaluation Configuration (Script 4)
    # ========================================================================
    
    # LLM API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # LLM Processing Configuration
    MODELS_TO_TEST: Optional[str] = os.getenv("MODELS_TO_TEST")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "512"))
    TIMEOUT: int = int(os.getenv("TIMEOUT", "30"))
    
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

class ConfigManager:
    """Manages configuration loading and validation."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config: Optional[dict] = None
        self.script_dir = Path(__file__).parent.parent.parent.resolve()
    
    def load_config(self) -> bool:
        """
        Load configuration from JSON file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            import json
            
            # Always resolve config path relative to the script's directory
            config_file = self.script_dir / self.config_path
            
            if not config_file.exists():
                raise FileNotFoundError(f"Config file not found: {config_file}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # Validate configuration
            if not self._validate_config():
                return False
            
            print(f"✓ Configuration loaded from {config_file}")
            return True
            
        except FileNotFoundError:
            print(f"❌ Config file not found: {self.config_path}")
            print("Please copy config.json.template to config.json and fill in your credentials")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in config file: {e}")
            return False
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return False
    
    def _validate_config(self) -> bool:
        """
        Validate the loaded configuration.
        
        Returns:
            True if valid, False otherwise
        """
        if not self.config:
            print("❌ No configuration loaded")
            return False
        
        # Check for required sections
        required_sections = ['credentials']
        for section in required_sections:
            if section not in self.config:
                print(f"❌ Missing required config section: {section}")
                return False
        
        # Validate credentials
        credentials = self.config.get('credentials', {})
        if not credentials.get('username'):
            print("❌ Username not found in config file")
            return False
        
        if not credentials.get('password'):
            print("❌ Password not found in config file")
            return False
        
        # Set default settings if not present
        if 'settings' not in self.config:
            self.config['settings'] = {}
        
        # Set default values for settings
        default_settings = {
            'headless': False,
            'timeout': 30000,
            'screenshot_delay': 2000,
            'viewport_width': 1920,
            'viewport_height': 1080,
            'user_agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36'),
            'use_state_persistence': True,
            'state_file': 'browser_state.json',
            'check_login_status': True
        }
        
        for key, default_value in default_settings.items():
            if key not in self.config['settings']:
                self.config['settings'][key] = default_value
        
        print("✓ Configuration validated successfully")
        return True
    
    def get_credentials(self) -> dict:
        """Get user credentials."""
        if not self.config:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        return self.config.get('credentials', {})
    
    def get_settings(self) -> dict:
        """Get application settings."""
        if not self.config:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        return self.config.get('settings', {})
    
    def get_setting(self, key: str, default=None):
        """Get a specific setting value."""
        if not self.config:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        return self.config.get('settings', {}).get(key, default)
    
    def get_browser_config(self) -> dict:
        """Get browser-specific configuration."""
        settings = self.get_settings()
        return {
            'headless': settings.get('headless', False),
            'viewport': {
                'width': settings.get('viewport_width', 1920),
                'height': settings.get('viewport_height', 1080)
            },
            'user_agent': settings.get('user_agent'),
            'timeout': settings.get('timeout', 30000)
        }
    
    def is_loaded(self) -> bool:
        """Check if configuration is loaded."""
        return self.config is not None
    
    def use_state_persistence(self) -> bool:
        """Check if state persistence is enabled."""
        return self.get_setting('use_state_persistence', True)
    
    def get_state_file(self) -> str:
        """Get the state file path."""
        return self.get_setting('state_file', 'browser_state.json')
    
    def get_username(self) -> str:
        """Get username from credentials."""
        credentials = self.get_credentials()
        return credentials.get('username', '')
    
    def get_password(self) -> str:
        """Get password from credentials."""
        credentials = self.get_credentials()
        return credentials.get('password', '')


# Validate configuration on import
Config.validate()