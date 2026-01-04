"""Filter Node - Identifies Chinese scholars studying abroad"""

from xpinyin import Pinyin
import logging

from app.agents.state import AgentState

logger = logging.getLogger(__name__)

# Initialize Pinyin converter
pinyin = Pinyin()

# Keywords indicating mainland China (these should be SKIPPED as they're not "overseas")
MAINLAND_CHINA_KEYWORDS = [
    "tsinghua", "peking university", "pku", "beijing", "shanghai",
    "fudan", "zhejiang university", "nanjing", "china", "chinese academy",
    "cas", "ustc", "harbin", "wuhan", "xi'an", "chengdu", "guangzhou"
]


def is_chinese_name(name: str) -> bool:
    """
    Check if a name appears to be Chinese using Pinyin conversion.
    
    Args:
        name: Full name to check
        
    Returns:
        True if the name appears to be Chinese
    """
    try:
        # Convert to pinyin - if it's already pinyin/English, it won't change much
        pinyin_result = pinyin.get_pinyin(name, '')
        
        # Simple heuristic: If the name is short (2-4 characters) and has Chinese characters
        # Or if the name contains common Chinese surname patterns
        
        # Check for Chinese characters directly
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in name)
        
        if has_chinese:
            return True
        
        # Common Chinese surnames in English
        common_surnames = [
            'wang', 'li', 'zhang', 'liu', 'chen', 'yang', 'huang', 'zhao',
            'wu', 'zhou', 'xu', 'sun', 'ma', 'zhu', 'hu', 'guo', 'he', 'gao',
            'lin', 'luo', 'zheng', 'liang', 'song', 'tang', 'xu', 'han', 'feng',
            'xie', 'yu', 'peng', 'cao'
        ]
        
        name_lower = name.lower()
        first_word = name_lower.split()[0] if name_lower.split() else ""
        
        return first_word in common_surnames
        
    except Exception as e:
        logger.warning(f"Pinyin check failed for '{name}': {str(e)}")
        return False


def is_mainland_china(affiliation: str) -> bool:
    """
    Check if affiliation is in mainland China.
    
    Args:
        affiliation: Institution/affiliation string
        
    Returns:
        True if affiliation is in mainland China (should be skipped)
    """
    aff_lower = affiliation.lower()
    return any(keyword in aff_lower for keyword in MAINLAND_CHINA_KEYWORDS)


def filter_node(state: AgentState) -> AgentState:
    """
    Node 2: Filter
    Marks candidates as SKIPPED if they are:
    1. Not Chinese names, OR
    2. Based in mainland China (not "overseas")
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with filtering applied
    """
    logger.info("[FilterNode] Starting filtering process")
    
    candidates = state["candidates"]
    
    for idx, candidate in enumerate(candidates):
        if candidate.status != "PENDING":
            continue
        
        # Check 1: Is the name Chinese?
        name_is_chinese = is_chinese_name(candidate.name)
        
        # Check 2: Is affiliation in mainland China?
        is_mainland = is_mainland_china(candidate.affiliation)
        
        # Skip if not Chinese OR if based in mainland China
        if not name_is_chinese:
            candidate.status = "SKIPPED"
            candidate.skip_reason = "Name does not appear to be Chinese"
            logger.info(f"  [{idx}] SKIP: {candidate.name} - Not Chinese name")
            
        elif is_mainland:
            candidate.status = "SKIPPED"
            candidate.skip_reason = "Affiliation is in mainland China (not overseas)"
            logger.info(f"  [{idx}] SKIP: {candidate.name} - Mainland China affiliation")
        
        else:
            logger.info(f"  [{idx}] PASS: {candidate.name} ({candidate.affiliation})")
    
    # Count results
    pending_count = sum(1 for c in candidates if c.status == "PENDING")
    skipped_count = sum(1 for c in candidates if c.status == "SKIPPED")
    
    logger.info(f"[FilterNode] Complete: {pending_count} to process, {skipped_count} skipped")
    
    return state

