"""SiliconFlow LLM客户端初始化"""

from langchain_openai import ChatOpenAI
from app.core.config import settings


def get_llm_client() -> ChatOpenAI:
    """
    初始化并返回为SiliconFlow配置的ChatOpenAI客户端
    
    Returns:
        ChatOpenAI: 已配置的LLM客户端
    """
    return ChatOpenAI(
        base_url=settings.SILICONFLOW_BASE_URL,
        api_key=settings.SILICONFLOW_API_KEY,
        model=settings.SILICONFLOW_MODEL,
        temperature=0.1,  # 低温度用于结构化提取
        max_tokens=2000,
    )


# 全局LLM实例（懒加载）
_llm_instance = None


def get_llm() -> ChatOpenAI:
    """获取或创建全局LLM实例"""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = get_llm_client()
    return _llm_instance

