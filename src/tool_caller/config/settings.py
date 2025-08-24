
import os

from pydantic_settings import BaseSettings
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

class LLMSettings(BaseSettings):
    """Settings for a single LLM provider"""
    api_key: str
    model: str
    max_tokens: int = 1000
    temperature: float = 0.1


class Settings(BaseSettings):
    """Application settings"""

    # Multiple LLM configurations
    llms: Dict[str, LLMSettings] = {
        "openai": LLMSettings(api_key="", model="gpt-4"),
        "anthropic": LLMSettings(api_key="", model="claude-3-sonnet-20240229"),
        # Gemini offers free API calls
        "gemini": LLMSettings(api_key=os.getenv("GEMINI_API_KEY"), model="gemini-1.5-pro")
    }

    
    default_llm_provider: str = "gemini"
    # Tool API keys
    weather_api_key: Optional[str] = None

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    # Performance
    max_concurrent_tools: int = 5
    tool_timeout: float = 30.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Return a singleton settings instance"""
    return Settings()
