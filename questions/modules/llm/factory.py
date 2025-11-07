"""Factory for creating LLM providers based on configuration."""

import os
from typing import List, Dict, Any, Optional
from .base import LLMProvider
from .openai_provider import OpenAIProvider
from .google_provider import GoogleProvider
from .anthropic_provider import AnthropicProvider
from ..core.exceptions import ConfigurationError


class LLMConfig:
    """Configuration for LLM providers."""
    
    # Model configurations
    MODELS = {
        'openai': ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'],
        'google': ['gemini-2.5-flash-lite', 'gemini-2.5-flash', 'gemini-2.5-pro'],
        'anthropic': ['claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307']
    }
    
    # Processing settings
    TEMPERATURE = float(os.getenv('TEMPERATURE', '0.0'))
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', '512'))
    TIMEOUT = int(os.getenv('TIMEOUT', '30'))
    
    # Models to test (from environment variable)
    MODELS_TO_TEST = [m.strip() for m in os.getenv('MODELS_TO_TEST', '').split(',') if m.strip()]


def create_llm_provider(provider_type: str, model_name: str, **kwargs) -> LLMProvider:
    """
    Create an LLM provider instance.
    
    Args:
        provider_type: Type of provider ('openai', 'google', 'anthropic')
        model_name: Name of the model
        **kwargs: Additional provider-specific parameters
        
    Returns:
        LLMProvider instance
        
    Raises:
        ConfigurationError: If provider type is invalid or not available
    """
    # Set default parameters
    config = {
        'temperature': kwargs.get('temperature', LLMConfig.TEMPERATURE),
        'max_tokens': kwargs.get('max_tokens', LLMConfig.MAX_TOKENS),
    }
    
    if provider_type == 'openai':
        config['timeout'] = kwargs.get('timeout', LLMConfig.TIMEOUT)
        provider = OpenAIProvider(model_name, **config)
    elif provider_type == 'google':
        provider = GoogleProvider(model_name, **config)
    elif provider_type == 'anthropic':
        config['timeout'] = kwargs.get('timeout', LLMConfig.TIMEOUT)
        provider = AnthropicProvider(model_name, **config)
    else:
        raise ConfigurationError(f"Unsupported provider type: {provider_type}")
    
    if not provider.is_available():
        raise ConfigurationError(f"{provider_type} provider is not available. Check API keys and dependencies.")
    
    return provider


def create_providers_from_config(models_to_test: Optional[List[str]] = None) -> List[LLMProvider]:
    """
    Create LLM providers based on configuration.
    
    Args:
        models_to_test: List of model specifications to test
        
    Returns:
        List of initialized LLM providers
        
    Raises:
        ConfigurationError: If no providers can be initialized
    """
    providers = []
    
    # Determine which models to test
    if models_to_test:
        selected_models = models_to_test
    elif LLMConfig.MODELS_TO_TEST:
        # Handle models from .env file - they might not have provider prefix
        selected_models = []
        for model in LLMConfig.MODELS_TO_TEST:
            model = model.strip()
            if not model:
                continue
            # If model doesn't have provider prefix, try to determine it
            if not any(model.startswith(f"{provider}/") for provider in ['openai', 'google', 'anthropic']):
                # Try to match with known models
                if model in LLMConfig.MODELS['google']:
                    selected_models.append(f"google/{model}")
                elif model in LLMConfig.MODELS['openai']:
                    selected_models.append(f"openai/{model}")
                elif model in LLMConfig.MODELS['anthropic']:
                    selected_models.append(f"anthropic/{model}")
                else:
                    # Default to google for unknown models
                    selected_models.append(f"google/{model}")
            else:
                selected_models.append(model)
    else:
        selected_models = []
        # Add all available models based on API keys
        if os.getenv('OPENAI_API_KEY'):
            selected_models.extend([f"openai/{m}" for m in LLMConfig.MODELS['openai']])
        if os.getenv('GOOGLE_API_KEY'):
            selected_models.extend([f"google/{m}" for m in LLMConfig.MODELS['google']])
        if os.getenv('ANTHROPIC_API_KEY'):
            selected_models.extend([f"anthropic/{m}" for m in LLMConfig.MODELS['anthropic']])
    
    # Initialize providers
    for model_spec in selected_models:
        try:
            if model_spec.startswith('openai/'):
                model_name = model_spec[7:]  # Remove 'openai/' prefix
                if model_name in LLMConfig.MODELS['openai']:
                    provider = create_llm_provider('openai', model_name)
                    providers.append(provider)
            elif model_spec.startswith('google/'):
                model_name = model_spec[7:]  # Remove 'google/' prefix
                if model_name in LLMConfig.MODELS['google']:
                    provider = create_llm_provider('google', model_name)
                    providers.append(provider)
            elif model_spec.startswith('anthropic/'):
                model_name = model_spec[10:]  # Remove 'anthropic/' prefix
                if model_name in LLMConfig.MODELS['anthropic']:
                    provider = create_llm_provider('anthropic', model_name)
                    providers.append(provider)
            else:
                print(f"Warning: Unknown model specification: {model_spec}")
        except Exception as e:
            print(f"Warning: Failed to initialize {model_spec}: {e}")
    
    if not providers:
        raise ConfigurationError("No LLM providers could be initialized. Please check your API keys and dependencies.")
    
    return providers


def get_available_providers() -> Dict[str, Any]:
    """
    Get information about available providers.
    
    Returns:
        Dictionary with provider availability information
    """
    providers_info = {}
    
    for provider_type in ['openai', 'google', 'anthropic']:
        try:
            # Try to create a provider with the first available model
            models = LLMConfig.MODELS.get(provider_type, [])
            if models:
                provider = create_llm_provider(provider_type, models[0])
                providers_info[provider_type] = {
                    'available': True,
                    'models': models,
                    'info': provider.get_provider_info()
                }
        except Exception as e:
            providers_info[provider_type] = {
                'available': False,
                'models': LLMConfig.MODELS.get(provider_type, []),
                'error': str(e)
            }
    
    return providers_info


def print_providers_status():
    """Print status of all available providers."""
    print("\n=== LLM Providers Status ===")
    
    providers_info = get_available_providers()
    
    for provider_name, info in providers_info.items():
        status = "✓ Available" if info["available"] else "✗ Not Available"
        print(f"{provider_name.upper()}: {status}")
        
        if not info["available"] and "error" in info:
            print(f"  Error: {info['error']}")
        elif info["available"] and "info" in info:
            provider_info = info["info"]
            print(f"  Models: {', '.join(info['models'])}")
            print(f"  Temperature: {provider_info.get('temperature', 'N/A')}")
            print(f"  Max Tokens: {provider_info.get('max_tokens', 'N/A')}")
    
    print("=" * 30)