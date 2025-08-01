"""
Flexible provider configuration for LLM models with fallback support.
Based on examples/main_agent_reference/providers.py pattern.
"""

from typing import Optional, Union
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.fallback import FallbackModel
from settings import settings


def get_llm_model(model_choice: Optional[str] = None) -> Union[OpenAIModel, AnthropicModel, GeminiModel, FallbackModel]:
    """
    Get LLM model configuration based on environment variables with fallback support.
    
    Args:
        model_choice: Optional override for model choice
    
    Returns:
        Configured model with fallback strategy
    """
    llm_choice = model_choice or settings.llm_model
    
    try:
        # Determine provider based on settings
        if settings.llm_provider.lower() == "gemini":
            # Primary model: Gemini
            gemini_provider = GoogleGLAProvider(api_key=settings.llm_api_key)
            primary_model = GeminiModel(llm_choice, provider=gemini_provider)
        elif settings.llm_provider.lower() == "anthropic":
            # Primary model: Anthropic
            anthropic_provider = AnthropicProvider(api_key=settings.llm_api_key)
            primary_model = AnthropicModel(llm_choice, provider=anthropic_provider)
        else:
            # Primary model: OpenAI (default)
            openai_provider = OpenAIProvider(
                base_url=settings.llm_base_url,
                api_key=settings.llm_api_key
            )
            primary_model = OpenAIModel(llm_choice, provider=openai_provider)
        
        # Fallback models if available
        fallback_models = []
        
        # Try to add other providers as fallback if available
        try:
            # Check if Anthropic API key is available and not the primary
            anthropic_key = getattr(settings, 'anthropic_api_key', None)
            if anthropic_key and settings.llm_provider.lower() != "anthropic":
                anthropic_provider = AnthropicProvider(api_key=anthropic_key)
                fallback_models.append(
                    AnthropicModel('claude-3-5-haiku-20241022', provider=anthropic_provider)
                )
        except Exception:
            pass  # Anthropic not available, continue without it
        
        # Return fallback model if we have alternatives
        if fallback_models:
            return FallbackModel([primary_model] + fallback_models)
        else:
            return primary_model
            
    except Exception as e:
        # For testing without proper API keys, return a basic model
        if settings.app_env == "testing":
            provider = OpenAIProvider(
                base_url=settings.llm_base_url or "https://api.openai.com/v1",
                api_key="test-key"
            )
            return OpenAIModel("gpt-4o-mini", provider=provider)
        else:
            raise ValueError(f"Failed to configure LLM model: {e}")


def get_model_info() -> dict:
    """
    Get information about current model configuration.
    
    Returns:
        Dictionary with model configuration info
    """
    return {
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "llm_base_url": settings.llm_base_url,
        "app_env": settings.app_env,
        "debug": settings.debug,
        "fallback_enabled": True,  # Always try to enable fallback
    }


def validate_llm_configuration() -> bool:
    """
    Validate that LLM configuration is properly set.
    
    Returns:
        True if configuration is valid
    """
    try:
        # Check if we can create a model instance
        model = get_llm_model()
        return True
    except Exception as e:
        print(f"LLM configuration validation failed: {e}")
        return False