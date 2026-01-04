"""HTTP Verification and Content Checking Tools"""

import httpx
from bs4 import BeautifulSoup
from typing import Optional, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


async def check_url_connectivity(url: str, timeout: int = 10) -> Tuple[bool, int]:
    """
    Check if a URL is accessible.
    
    Args:
        url: URL to check
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (is_accessible, status_code)
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            response = await client.get(url)
            return (response.status_code == 200, response.status_code)
    except Exception as e:
        logger.warning(f"Connectivity check failed for {url}: {str(e)}")
        return (False, 0)


async def fetch_page_text(url: str, timeout: int = 15) -> Optional[str]:
    """
    Fetch and extract text content from a webpage.
    
    Args:
        url: URL to scrape
        timeout: Request timeout in seconds
        
    Returns:
        Extracted text content or None if failed
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                logger.warning(f"Non-200 status for {url}: {response.status_code}")
                return None
            
            # Parse HTML and extract text
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean it
            text = soup.get_text(separator=' ', strip=True)
            
            # Limit text length to avoid token overflow
            max_chars = 10000
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            return text
            
    except Exception as e:
        logger.error(f"Failed to fetch page text from {url}: {str(e)}")
        return None


def semantic_match(page_text: str, name: str, affiliation: str) -> bool:
    """
    Check if page content semantically matches the expected scholar.
    
    Args:
        page_text: Extracted text from the webpage
        name: Scholar's name to verify
        affiliation: Expected affiliation
        
    Returns:
        True if the page appears to belong to the target scholar
    """
    if not page_text:
        return False
    
    page_lower = page_text.lower()
    name_lower = name.lower()
    affiliation_lower = affiliation.lower()
    
    # Check 1: Name must be present
    name_present = name_lower in page_lower
    
    # Check 2: Affiliation or affiliation keywords present
    affiliation_present = affiliation_lower in page_lower
    
    # For universities, check short forms (e.g., "CMU" for "Carnegie Mellon University")
    affiliation_keywords = affiliation.split()
    keyword_match = any(keyword.lower() in page_lower for keyword in affiliation_keywords if len(keyword) > 3)
    
    return name_present and (affiliation_present or keyword_match)


def extract_email_simple(page_text: str) -> Optional[str]:
    """
    Simple email extraction from page text.
    
    Args:
        page_text: Page text content
        
    Returns:
        First email found or None
    """
    import re
    if not page_text:
        return None
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, page_text)
    
    # Filter out common false positives
    blocked = ['example.com', 'test.com', 'email.com']
    valid_emails = [m for m in matches if not any(b in m.lower() for b in blocked)]
    
    return valid_emails[0] if valid_emails else None

