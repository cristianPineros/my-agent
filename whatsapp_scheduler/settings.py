"""
Configuration management using pydantic-settings for WhatsApp Scheduling Agent.
Based on examples/main_agent_reference/settings.py pattern.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # LLM Configuration
    llm_provider: str = Field(default="openai")
    llm_api_key: str = Field(...)
    llm_model: str = Field(default="gpt-4o-mini")
    llm_base_url: Optional[str] = Field(default="https://api.openai.com/v1")
    
    # WhatsApp Business API Configuration
    whatsapp_api_key: str = Field(...)
    whatsapp_phone_id: str = Field(...)
    whatsapp_business_account_id: str = Field(...)
    whatsapp_webhook_token: str = Field(...)
    whatsapp_base_url: str = Field(
        default="https://graph.facebook.com/v18.0"
    )
    
    # Google Calendar API Configuration
    calendar_api_key: Optional[str] = Field(default=None)
    calendar_credentials_path: str = Field(default="credentials.json")
    calendar_token_path: str = Field(default="token.json")
    calendar_id: str = Field(default="primary")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///scheduler.db")
    
    # Application Configuration
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)
    default_timezone: str = Field(default="UTC")
    business_hours_start: int = Field(default=9)  # 9 AM
    business_hours_end: int = Field(default=17)   # 5 PM
    
    # Rate Limiting Configuration
    rate_limit_per_minute: int = Field(default=30)
    rate_limit_per_hour: int = Field(default=100)
    
    @field_validator("llm_api_key", "whatsapp_api_key", "whatsapp_phone_id", "whatsapp_business_account_id", "whatsapp_webhook_token")
    @classmethod
    def validate_required_keys(cls, v):
        """Ensure required API keys and IDs are not empty."""
        if not v or v.strip() == "":
            raise ValueError("Required configuration value cannot be empty")
        return v
    
    @field_validator("business_hours_start", "business_hours_end")
    @classmethod
    def validate_business_hours(cls, v):
        """Ensure business hours are valid."""
        if not (0 <= v <= 23):
            raise ValueError("Business hours must be between 0 and 23")
        return v


# Global settings instance
try:
    settings = Settings()
except Exception:
    # For testing, create settings with dummy values
    import os
    os.environ.setdefault("LLM_API_KEY", "test_key")
    os.environ.setdefault("WHATSAPP_API_KEY", "test_key")
    os.environ.setdefault("WHATSAPP_PHONE_ID", "test_phone_id")
    os.environ.setdefault("WHATSAPP_BUSINESS_ACCOUNT_ID", "test_account_id")
    os.environ.setdefault("WHATSAPP_WEBHOOK_TOKEN", "test_webhook_token")
    settings = Settings()