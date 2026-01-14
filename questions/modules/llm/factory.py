"""Factory for creating LLM providers based on configuration."""

import os
from typing import List, Dict, Any, Optional
from .base import LLMProvider
from .openai_provider import OpenAIProvider
from .google_provider import GoogleProvider
from .anthropic_provider import AnthropicProvider
from .harvard_bedrock_provider import HarvardBedrockProvider
from ..core.exceptions import ConfigurationError


class LLMConfig:
    """Configuration for LLM providers."""
    
    # Model configurations
    MODELS = {
        'openai': [
          "gpt-4.1-2025-04-14",
          "gpt-5-2025-08-07",
          "gpt-5.2-2025-12-11",
          "gpt-5.2-pro-2025-12-11",
          "gpt-5-mini-2025-08-07",
          "gpt-5-nano-2025-08-07",
        ],
        'google': [
            'gemini-2.5-flash-lite',
            'gemini-2.5-flash',
            'gemini-2.5-pro',
            'gemini-2.5-flash-preview-09-2025',
        ],
        'anthropic': [
            'claude-sonnet-4-5-20250929',
            'claude-haiku-4-5-20251001',
            'claude-opus-4-1-20250805',
        ],
        'harvard': [
            # V2 models (with us. prefix) - Anthropic Claude
            'us.anthropic.claude-opus-4-5-20251101-v1:0',
            'us.anthropic.claude-haiku-4-5-20251001-v1:0',
            'us.anthropic.claude-sonnet-4-5-20250929-v1:0',
            'us.anthropic.claude-sonnet-4-20250514-v1:0',
            'us.anthropic.claude-opus-4-20250514-v1:0',
            'us.anthropic.claude-3-5-sonnet-20240620-v1:0',
            'us.anthropic.claude-3-5-haiku-20241022-v1:0',
            'us.anthropic.claude-3-haiku-20240307-v1:0',
            # V2 models - Meta Llama
            'us.meta.llama4-maverick-17b-instruct-v1:0',
            'us.meta.llama4-scout-17b-instruct-v1:0',
            'us.meta.llama3-3-70b-instruct-v1:0',
            'us.meta.llama3-2-1b-instruct-v1:0',
            'us.meta.llama3-2-3b-instruct-v1:0',
            'us.meta.llama3-2-11b-instruct-v1:0',
            'us.meta.llama3-1-8b-instruct-v1:0',
            'us.meta.llama3-1-70b-instruct-v1:0',
            'us.meta.llama3-1-405b-instruct-v1:0',
            # V2 models - Mistral
            'us.mistral.pixtral-large-2502-v1:0',
            # V1 models (legacy, without us. prefix)
            'anthropic.claude-3-5-sonnet-20241022-v2:0',
            'anthropic.claude-3-5-haiku-20241022-v1:0',
            'anthropic.claude-3-opus-20240229-v1:0',
            'meta.llama3-3-70b-instruct-v1:0',
            'meta.llama3-1-405b-instruct-v1:0',
        ]
    }
    
    # Processing settings
    TEMPERATURE = float(os.getenv('TEMPERATURE', '0.0'))
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', '512'))
    TIMEOUT = int(os.getenv('TIMEOUT', '30'))
    
    # Harvard Bedrock API settings
    HARVARD_API_VERSION = os.getenv('HARVARD_API_VERSION', 'v2')
    
    # Models to test (from environment variable)
    MODELS_TO_TEST = [m.strip() for m in os.getenv('MODELS_TO_TEST', '').split(',') if m.strip()]


def create_llm_provider(provider_type: str, model_name: str, **kwargs) -> LLMProvider:
    """
    Create an LLM provider instance.
    
    Args:
        provider_type: Type of provider ('openai', 'google', 'anthropic', 'harvard')
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
        # Extend timeout for reasoning-heavy GPT-5 model unless caller provided a higher value
        if model_name == "gpt-5-2025-08-07" and config['timeout'] < 120:
            config['timeout'] = 120
        provider = OpenAIProvider(model_name, **config)
    elif provider_type == 'google':
        provider = GoogleProvider(model_name, **config)
    elif provider_type == 'anthropic':
        config['timeout'] = kwargs.get('timeout', LLMConfig.TIMEOUT)
        provider = AnthropicProvider(model_name, **config)
    elif provider_type == 'harvard':
        config['timeout'] = kwargs.get('timeout', LLMConfig.TIMEOUT)
        config['api_version'] = kwargs.get('api_version', LLMConfig.HARVARD_API_VERSION)
        provider = HarvardBedrockProvider(model_name, **config)
    else:
        raise ConfigurationError(f"Unsupported provider type: {provider_type}")
    
    if not provider.is_available():
        raise ConfigurationError(f"{provider_type} provider is not available. Check API keys and dependencies.")
    
    return provider


def _normalize_model_specs(models: List[str]) -> List[str]:
    """
    Normalize model specifications by adding provider prefixes where needed.
    
    Args:
        models: List of model specifications (with or without provider prefix)
        
    Returns:
        List of normalized model specifications with provider prefixes
    """
    normalized = []
    
    for model in models:
        model = model.strip()
        if not model:
            continue
        
        # If model already has a provider prefix, keep it as is
        if any(model.startswith(f"{provider}/") for provider in ['openai', 'google', 'anthropic', 'harvard']):
            normalized.append(model)
        else:
            # Try to match with known models and add appropriate prefix
            if model in LLMConfig.MODELS['google']:
                normalized.append(f"google/{model}")
            elif model in LLMConfig.MODELS['openai']:
                normalized.append(f"openai/{model}")
            elif model in LLMConfig.MODELS['anthropic']:
                normalized.append(f"anthropic/{model}")
            elif model in LLMConfig.MODELS['harvard']:
                normalized.append(f"harvard/{model}")
            else:
                # Default to google for unknown models
                normalized.append(f"google/{model}")
    
    return normalized


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
        selected_models = _normalize_model_specs(models_to_test)
    elif LLMConfig.MODELS_TO_TEST:
        # Handle models from .env file - they might not have provider prefix
        selected_models = _normalize_model_specs(LLMConfig.MODELS_TO_TEST)
    else:
        selected_models = []
        # Add all available models based on API keys
        if os.getenv('OPENAI_API_KEY'):
            selected_models.extend([f"openai/{m}" for m in LLMConfig.MODELS['openai']])
        if os.getenv('GOOGLE_API_KEY'):
            selected_models.extend([f"google/{m}" for m in LLMConfig.MODELS['google']])
        if os.getenv('ANTHROPIC_API_KEY'):
            selected_models.extend([f"anthropic/{m}" for m in LLMConfig.MODELS['anthropic']])
        if os.getenv('HARVARD_API_KEY'):
            selected_models.extend([f"harvard/{m}" for m in LLMConfig.MODELS['harvard']])
    
    # Final safety check: normalize any remaining models just in case
    selected_models = _normalize_model_specs(selected_models) if selected_models else []
    
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
            elif model_spec.startswith('harvard/'):
                model_name = model_spec[8:]  # Remove 'harvard/' prefix
                if model_name in LLMConfig.MODELS['harvard']:
                    provider = create_llm_provider('harvard', model_name)
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
    
    for provider_type in ['openai', 'google', 'anthropic', 'harvard']:
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