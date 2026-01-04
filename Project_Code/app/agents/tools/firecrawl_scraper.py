"""Firecrawl增强网页抓取工具"""

import logging
from typing import Optional, Dict
from app.core.config import settings

logger = logging.getLogger(__name__)

# 检查Firecrawl是否可用
FIRECRAWL_AVAILABLE = False
try:
    if settings.FIRECRAWL_ENABLED and settings.FIRECRAWL_API_KEY:
        from firecrawl import FirecrawlApp
        FIRECRAWL_AVAILABLE = True
        logger.info("Firecrawl集成已启用")
except ImportError:
    logger.warning("Firecrawl包未安装。安装命令: pip install firecrawl-py")
except Exception as e:
    logger.warning(f"Firecrawl初始化失败: {str(e)}")


async def firecrawl_scrape_page(url: str, timeout: int = 30) -> Optional[Dict[str, str]]:
    """
    使用 Firecrawl 抓取网页内容（增强版）
    
    功能优势：
    - ✅ JavaScript渲染支持 (React/Vue等SPA)
    - ✅ 智能反爬虫绕过 (Cloudflare等)
    - ✅ 自动内容清洗 (去除广告、导航栏)
    - ✅ Markdown格式输出 (结构化，便于LLM理解)
    
    Args:
        url: 目标URL
        timeout: 超时时间（秒）
        
    Returns:
        Dict包含 'markdown', 'html', 'text' 或 None（失败时）
    """
    if not FIRECRAWL_AVAILABLE:
        logger.debug("Firecrawl not available, skipping")
        return None
    
    try:
        # 初始化 Firecrawl 客户端
        app = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)
        
        # 抓取配置
        scrape_options = {
            'formats': ['markdown', 'html'],  # 同时获取Markdown和HTML
            'onlyMainContent': True,  # 仅提取主要内容
            'waitFor': 3000,  # 等待3秒让JavaScript渲染
            'timeout': timeout * 1000,  # 转换为毫秒
        }
        
        logger.info(f"[Firecrawl] Scraping: {url}")
        
        # 执行抓取
        result = app.scrape_url(url, params=scrape_options)
        
        if result and result.get('success'):
            data = result.get('data', {})
            
            # 提取内容
            markdown = data.get('markdown', '')
            html = data.get('html', '')
            
            # Markdown优先（更结构化，适合LLM）
            text_content = markdown if markdown else html
            
            if not text_content:
                logger.warning(f"[Firecrawl] Empty content from {url}")
                return None
            
            logger.info(f"[Firecrawl] ✓ Success: {len(text_content)} chars extracted")
            
            return {
                'markdown': markdown,
                'html': html,
                'text': text_content,
                'source': 'firecrawl'
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.warning(f"[Firecrawl] Failed: {error_msg}")
            return None
            
    except Exception as e:
        logger.error(f"[Firecrawl] Exception: {str(e)}")
        return None


async def firecrawl_search_and_scrape(query: str, max_results: int = 3) -> Optional[list]:
    """
    使用 Firecrawl 的搜索功能（如果可用）
    
    Args:
        query: 搜索查询
        max_results: 最大结果数
        
    Returns:
        搜索结果列表或None
    """
    if not FIRECRAWL_AVAILABLE:
        return None
    
    try:
        app = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)
        
        # 注意：Firecrawl的搜索功能可能需要不同的API端点
        # 这里提供一个框架，具体实现需要根据Firecrawl API文档调整
        logger.info(f"[Firecrawl Search] Query: {query}")
        
        # 如果Firecrawl提供搜索API，在这里调用
        # results = app.search(query, limit=max_results)
        
        # 目前Firecrawl主要用于抓取，搜索仍使用DuckDuckGo
        return None
        
    except Exception as e:
        logger.error(f"[Firecrawl Search] Exception: {str(e)}")
        return None


def is_firecrawl_enabled() -> bool:
    """
    检查 Firecrawl 是否已启用
    
    Returns:
        True if enabled and available
    """
    return FIRECRAWL_AVAILABLE

