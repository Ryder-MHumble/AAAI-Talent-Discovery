"""使用Pydantic Settings进行配置管理"""

from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """从环境变量加载的应用配置"""
    
    # SiliconFlow LLM 配置
    SILICONFLOW_API_KEY: str
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"
    SILICONFLOW_MODEL: str = "deepseek-ai/DeepSeek-V3"
    
    # 应用设置
    APP_ENV: Literal["DEV", "PROD"] = "DEV"
    API_VERSION: str = "v1"
    CONCURRENT_SEARCHES: int = 3
    
    # AAAI-26 URL地址
    AAAI_INVITED_SPEAKERS_URL: str = "https://aaai.org/conference/aaai/aaai-26/invited-speakers/"
    AAAI_TECHNICAL_TRACK_URL: str = "https://aaai.org/conference/aaai/aaai-26/technical-track/"
    
    # Firecrawl 配置（可选 - 增强网页抓取）
    FIRECRAWL_API_KEY: str = ""  # 留空则使用httpx回退方案
    FIRECRAWL_ENABLED: bool = False  # 设为True以启用Firecrawl
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()

