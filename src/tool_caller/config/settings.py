
import os
import logging
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional, Dict
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)

class LLMSettings(BaseSettings):
    """Settings for a single LLM provider"""
    api_key: str
    model: str
    max_tokens: int = 1000
    temperature: float = 0.1


class Settings(BaseSettings):
    """Application settings"""


    ## Check if there is any api key available in the environment variables

    if not os.getenv("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEY is not set. Some features may not work.")
        raise ValueError("GEMINI_API_KEY is required but not set in environment variables.")
    
    if not os.getenv("WEATHER_API_KEY"):
        logger.warning("WEATHER_API_KEY is not set. Some features may not work.")



    # Multiple LLM configurations
    llms: Dict[str, LLMSettings] = {
        "openai": LLMSettings(api_key="", model="gpt-4"),
        "anthropic": LLMSettings(api_key="", model="claude-3-sonnet-20240229"),
        # Gemini offers free API calls
        "gemini": LLMSettings(api_key=os.getenv("GEMINI_API_KEY"), model="gemini-1.5-pro")
    }

    
    default_llm_provider: str = "gemini"
    # Tool API keys
    
    
    weather_api_key: Optional[str] = os.getenv("WEATHER_API_KEY")

    # Logging
    log_level: str = "INFO"
    project_root: Path = Path(__file__).resolve().parent
    log_file: Path =  "logs/app.log"

    # Debug print to verify
    print(f"Settings file: {Path(__file__).resolve()}")
    print(f"Project root: {project_root}")
    print(f"Log file: {log_file}")
    # Performance
    max_concurrent_tools: int = 5
    tool_timeout: float = 30.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Return a singleton settings instance"""
    return Settings()
