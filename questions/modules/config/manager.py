"""
Configuration management for Zanichelli exercise automation.

This module handles loading, validation, and management of configuration settings.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages configuration loading and validation."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config: Optional[Dict[str, Any]] = None
        self.script_dir = Path(__file__).parent.parent.parent.resolve()
    
    def load_config(self) -> bool:
        """
        Load configuration from JSON file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
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
                          'Chrome/120.0.0.0 Safari/537.36')
        }
        
        for key, default_value in default_settings.items():
            if key not in self.config['settings']:
                self.config['settings'][key] = default_value
        
        print("✓ Configuration validated successfully")
        return True
    
    def get_credentials(self) -> Dict[str, str]:
        """
        Get user credentials.
        
        Returns:
            Dictionary with username and password
        """
        if not self.config:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        
        return self.config.get('credentials', {})
    
    def get_settings(self) -> Dict[str, Any]:
        """
        Get application settings.
        
        Returns:
            Dictionary with application settings
        """
        if not self.config:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        
        return self.config.get('settings', {})
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a specific setting value.
        
        Args:
            key: Setting key
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        if not self.config:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        
        return self.config.get('settings', {}).get(key, default)
    
    def get_browser_config(self) -> Dict[str, Any]:
        """
        Get browser-specific configuration.
        
        Returns:
            Dictionary with browser configuration
        """
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
    
    def get_username(self) -> str:
        """Get username from credentials."""
        credentials = self.get_credentials()
        return credentials.get('username', '')
    
    def get_password(self) -> str:
        """Get password from credentials."""
        credentials = self.get_credentials()
        return credentials.get('password', '')
    
    def is_headless_mode(self) -> bool:
        """Check if headless mode is enabled."""
        return self.get_setting('headless', False)
    
    def get_timeout(self) -> int:
        """Get default timeout value."""
        return self.get_setting('timeout', 30000)
    
    def get_screenshot_delay(self) -> int:
        """Get screenshot delay value."""
        return self.get_setting('screenshot_delay', 2000)
    
    def create_template_config(self, template_path: str = "config.json.template") -> bool:
        """
        Create a template configuration file.
        
        Args:
            template_path: Path for the template file
            
        Returns:
            True if successful, False otherwise
        """
        template_config = {
            "credentials": {
                "username": "your_email_or_phone@example.com",
                "password": "your_password_here"
            },
            "settings": {
                "headless": False,
                "timeout": 30000,
                "screenshot_delay": 2000,
                "viewport_width": 1920,
                "viewport_height": 1080,
                "user_agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36")
            }
        }
        
        try:
            template_file = self.script_dir / template_path
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_config, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Template configuration created: {template_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating template config: {e}")
            return False
    
    def __str__(self) -> str:
        """String representation of the configuration."""
        if not self.config:
            return "ConfigManager(not loaded)"
        
        # Don't expose sensitive information
        safe_config = {
            'credentials': {'username': '***', 'password': '***'},
            'settings': self.config.get('settings', {})
        }
        
        return f"ConfigManager({safe_config})"