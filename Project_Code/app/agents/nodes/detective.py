"""侦探节点 - 搜索并发现候选人主页"""

import logging
from typing import Optional

from app.agents.state import AgentState
from app.agents.tools.search import search_scholar_homepage

logger = logging.getLogger(__name__)


def find_best_homepage_url(search_results: list, candidate_name: str, affiliation: str) -> Optional[str]:
    """
    分析搜索结果并选择最可能的主页URL
    
    Args:
        search_results: DuckDuckGo的搜索结果列表
        candidate_name: 候选人姓名
        affiliation: 要匹配的所属单位
        
    Returns:
        最佳匹配的URL或None
    """
    if not search_results:
        return None
    
    # URL选择的评分启发式
    best_url = None
    best_score = 0
    
    for result in search_results:
        url = result.get('url', '').lower()
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        
        score = 0
        
        # 正面信号
        if any(keyword in url for keyword in ['homepage', 'personal', 'people', 'faculty', 'profile', '~']):
            score += 3
        
        if any(keyword in title for keyword in ['homepage', 'home page', 'personal page']):
            score += 2
        
        # 大学域名是好的信号
        if any(domain in url for domain in ['.edu', '.ac.', affiliation.lower().replace(' ', '')[:10]]):
            score += 2
        
        # URL中包含姓名是强信号
        name_parts = candidate_name.lower().split()
        if any(part in url for part in name_parts if len(part) > 2):
            score += 4
        
        # 负面信号
        if any(keyword in url for keyword in ['linkedin', 'facebook', 'twitter', 'instagram', 'wikipedia']):
            score -= 5
        
        if any(keyword in url for keyword in ['pdf', 'paper', 'publication', 'arxiv']):
            score -= 2
        
        if score > best_score:
            best_score = score
            best_url = result['url']
    
    return best_url


async def detective_node(state: AgentState) -> AgentState:
    """
    节点3: 侦探
    使用搜索引擎搜索当前候选人的主页
    一次处理一个PENDING候选人
    
    Args:
        state: 当前智能体状态
        
    Returns:
        包含搜索结果的更新状态
    """
    candidates = state["candidates"]
    current_index = state["current_index"]
    
    # 查找下一个PENDING候选人
    while current_index < len(candidates):
        candidate = candidates[current_index]
        
        if candidate.status == "PENDING":
            logger.info(f"[侦探节点] 处理 #{current_index}: {candidate.name}")
            
            # 搜索主页
            search_results = search_scholar_homepage(candidate.name, candidate.affiliation)
            
            if search_results:
                # 查找最佳匹配URL
                best_url = find_best_homepage_url(search_results, candidate.name, candidate.affiliation)
                
                if best_url:
                    candidate.homepage = best_url
                    logger.info(f"[侦探节点] 找到URL: {best_url}")
                else:
                    logger.warning(f"[侦探节点] 搜索结果中没有找到合适的URL")
                    candidate.status = "FAILED"
                    candidate.skip_reason = "搜索结果中未找到合适的主页"
            else:
                logger.warning(f"[侦探节点] 搜索未返回结果")
                candidate.status = "FAILED"
                candidate.skip_reason = "搜索未返回结果"
            
            # 移动到下一个候选人
            state["current_index"] = current_index + 1
            return state
        
        current_index += 1
    
    # 没有更多PENDING候选人
    logger.info("[侦探节点] 没有更多待处理的候选人")
    state["current_index"] = current_index
    
    return state

