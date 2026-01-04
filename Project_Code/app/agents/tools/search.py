"""使用DuckDuckGo的搜索工具封装"""

from typing import List, Dict, Optional
from duckduckgo_search import DDGS
import logging

logger = logging.getLogger(__name__)


def search_scholar_homepage(name: str, affiliation: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    使用DuckDuckGo搜索学者主页
    
    Args:
        name: 学者全名
        affiliation: 当前所属单位/大学
        max_results: 返回的最大搜索结果数
        
    Returns:
        包含'title'、'url'和'snippet'的搜索结果列表
    """
    query = f'"{name}" "{affiliation}" homepage'
    logger.info(f"搜索: {query}")
    
    try:
        with DDGS() as ddgs:
            results = []
            for result in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", "")
                })
            
            logger.info(f"为{name}找到{len(results)}个结果")
            return results
            
    except Exception as e:
        logger.error(f"{name}搜索失败: {str(e)}")
        return []


def search_with_keywords(name: str, affiliation: str, keywords: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """
    使用额外关键词进行增强搜索（例如研究领域）
    
    Args:
        name: 学者全名
        affiliation: 当前所属单位
        keywords: 额外搜索词
        
    Returns:
        搜索结果列表
    """
    keyword_str = " ".join(keywords) if keywords else ""
    query = f'"{name}" "{affiliation}" {keyword_str} homepage OR profile OR "personal page"'
    
    try:
        with DDGS() as ddgs:
            results = []
            for result in ddgs.text(query, max_results=5):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", "")
                })
            return results
    except Exception as e:
        logger.error(f"增强搜索失败: {str(e)}")
        return []

