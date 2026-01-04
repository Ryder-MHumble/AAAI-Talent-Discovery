"""LLM Client Initialization for SiliconFlow"""

from langchain_openai import ChatOpenAI
from app.core.config import settings


def get_llm_client() -> ChatOpenAI:
    """
    Initialize and return a ChatOpenAI client configured for SiliconFlow.
    
    Returns:
        ChatOpenAI: Configured LLM client
    """
    return ChatOpenAI(
        base_url=settings.SILICONFLOW_BASE_URL,
        api_key=settings.SILICONFLOW_API_KEY,
        model=settings.SILICONFLOW_MODEL,
        temperature=0.1,  # Low temperature for structured extraction
        max_tokens=2000,
    )


# Global LLM instance (lazy initialization)
_llm_instance = None


def get_llm() -> ChatOpenAI:
    """Get or create the global LLM instance"""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = get_llm_client()
    return _llm_instance

