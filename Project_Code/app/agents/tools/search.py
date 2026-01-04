"""Search Tool Wrapper using DuckDuckGo"""

from typing import List, Dict, Optional
from duckduckgo_search import DDGS
import logging

logger = logging.getLogger(__name__)


def search_scholar_homepage(name: str, affiliation: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search for a scholar's homepage using DuckDuckGo.
    
    Args:
        name: Scholar's full name
        affiliation: Current affiliation/university
        max_results: Maximum number of search results to return
        
    Returns:
        List of search results with 'title', 'url', and 'snippet'
    """
    query = f'"{name}" "{affiliation}" homepage'
    logger.info(f"Searching for: {query}")
    
    try:
        with DDGS() as ddgs:
            results = []
            for result in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", "")
                })
            
            logger.info(f"Found {len(results)} results for {name}")
            return results
            
    except Exception as e:
        logger.error(f"Search failed for {name}: {str(e)}")
        return []


def search_with_keywords(name: str, affiliation: str, keywords: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """
    Enhanced search with additional keywords (e.g., research areas).
    
    Args:
        name: Scholar's full name
        affiliation: Current affiliation
        keywords: Additional search terms
        
    Returns:
        List of search results
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
        logger.error(f"Enhanced search failed: {str(e)}")
        return []

