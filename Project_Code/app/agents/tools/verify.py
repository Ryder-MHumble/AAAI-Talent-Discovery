"""HTTP验证和内容检查工具"""

import httpx
from bs4 import BeautifulSoup
from typing import Optional, Dict, Tuple
import logging
from app.agents.tools.firecrawl_scraper import firecrawl_scrape_page, is_firecrawl_enabled

logger = logging.getLogger(__name__)


async def check_url_connectivity(url: str, timeout: int = 10) -> Tuple[bool, int]:
    """
    检查URL是否可访问
    
    Args:
        url: 要检查的URL
        timeout: 请求超时时间（秒）
        
    Returns:
        元组(is_accessible, status_code)
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            response = await client.get(url)
            return (response.status_code == 200, response.status_code)
    except Exception as e:
        logger.warning(f"{url}连接检查失败: {str(e)}")
        return (False, 0)


async def fetch_page_text(url: str, timeout: int = 15) -> Optional[str]:
    """
    Fetch and extract text content from a webpage.
    
    使用双路由策略：
    1. 优先尝试 Firecrawl（如果启用）- 支持JS渲染、智能清洗
    2. 降级到 httpx + BeautifulSoup - 传统抓取方式
    
    Args:
        url: URL to scrape
        timeout: Request timeout in seconds
        
    Returns:
        Extracted text content or None if failed
    """
    # 策略1: 尝试使用 Firecrawl（增强抓取）
    if is_firecrawl_enabled():
        logger.info(f"[Fetch] Trying Firecrawl for: {url}")
        firecrawl_result = await firecrawl_scrape_page(url, timeout)
        
        if firecrawl_result:
            # Firecrawl 成功，使用其结果
            text = firecrawl_result.get('text', '')
            
            if text:
                # Limit text length to avoid token overflow
                max_chars = 10000
                if len(text) > max_chars:
                    text = text[:max_chars] + "..."
                
                logger.info(f"[Fetch] ✓ Firecrawl success: {len(text)} chars")
                return text
        
        # Firecrawl 失败，记录日志并降级
        logger.warning(f"[Fetch] Firecrawl failed for {url}, falling back to httpx")
    
    # 策略2: 降级到传统 httpx + BeautifulSoup
    try:
        logger.info(f"[Fetch] Using httpx for: {url}")
        
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                logger.warning(f"Non-200 status for {url}: {response.status_code}")
                return None
            
            # 解析HTML并提取文本
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 删除script和style元素
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 获取文本并清理
            text = soup.get_text(separator=' ', strip=True)
            
            # 限制文本长度以避免token溢出
            max_chars = 10000
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            logger.info(f"[获取] ✓ httpx成功: {len(text)}个字符")
            return text
            
    except Exception as e:
        logger.error(f"从{url}获取页面文本失败: {str(e)}")
        return None


def semantic_match(page_text: str, name: str, affiliation: str) -> bool:
    """
    检查页面内容是否与预期学者语义匹配
    
    Args:
        page_text: 从网页提取的文本
        name: 要验证的学者姓名
        affiliation: 预期所属单位
        
    Returns:
        如果页面看起来属于目标学者则返回True
    """
    if not page_text:
        return False
    
    page_lower = page_text.lower()
    name_lower = name.lower()
    affiliation_lower = affiliation.lower()
    
    # 检查1: 姓名必须存在
    name_present = name_lower in page_lower
    
    # 检查2: 所属单位或所属单位关键词存在
    affiliation_present = affiliation_lower in page_lower
    
    # 对于大学，检查缩写形式（例如"CMU"代表"Carnegie Mellon University"）
    affiliation_keywords = affiliation.split()
    keyword_match = any(keyword.lower() in page_lower for keyword in affiliation_keywords if len(keyword) > 3)
    
    return name_present and (affiliation_present or keyword_match)


def extract_email_simple(page_text: str) -> Optional[str]:
    """
    从页面文本中简单提取邮箱
    
    Args:
        page_text: 页面文本内容
        
    Returns:
        找到的第一个邮箱或None
    """
    import re
    if not page_text:
        return None
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, page_text)
    
    # 过滤常见的误报
    blocked = ['example.com', 'test.com', 'email.com']
    valid_emails = [m for m in matches if not any(b in m.lower() for b in blocked)]
    
    return valid_emails[0] if valid_emails else None

