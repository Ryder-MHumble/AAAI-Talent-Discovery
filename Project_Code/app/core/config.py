"""Configuration management using Pydantic Settings"""

from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # SiliconFlow LLM Configuration
    SILICONFLOW_API_KEY: str
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"
    SILICONFLOW_MODEL: str = "deepseek-ai/DeepSeek-V3"
    
    # Application Settings
    APP_ENV: Literal["DEV", "PROD"] = "DEV"
    API_VERSION: str = "v1"
    CONCURRENT_SEARCHES: int = 3
    
    # AAAI-26 URLs
    AAAI_INVITED_SPEAKERS_URL: str = "https://aaai.org/conference/aaai/aaai-26/invited-speakers/"
    AAAI_TECHNICAL_TRACK_URL: str = "https://aaai.org/conference/aaai/aaai-26/technical-track/"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

