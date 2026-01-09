"""侦探节点 - 搜索并发现候选人主页，集成AMiner学者验证"""

import logging
from typing import Optional

from app.agents.state import AgentState
from app.agents.tools.search import search_scholar_homepage
from app.agents.tools.aminer_api import aminer_api
from app.core.config import settings

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
    可选：集成AMiner API进行学者身份验证和信息补充
    一次处理一个PENDING候选人
    
    处理流程：
    1. 尝试通过AMiner API验证候选人身份（如果启用）
    2. 如果AMiner验证失败或未启用，使用DuckDuckGo搜索主页
    3. 补充候选人信息
    
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
            logger.info(f"[侦探节点] 处理 #{current_index}: {candidate.name} ({candidate.affiliation})")
            
            # 步骤1: 尝试使用AMiner API进行验证和补充（如果启用）
            aminer_enriched = False
            if settings.AMINER_ENABLED and settings.AMINER_API_KEY:
                try:
                    logger.info(f"[侦探节点] 尝试AMiner验证: {candidate.name}")
                    aminer_result = await aminer_api.validate_and_enrich(
                        name=candidate.name,
                        affiliation=candidate.affiliation,
                        email=candidate.email
                    )
                    
                    if aminer_result and aminer_result.get("is_verified"):
                        # 成功验证并补充信息
                        candidate.name_cn = aminer_result.get("name_cn")
                        candidate.email = aminer_result.get("email") or candidate.email
                        
                        # 存储interests作为研究方向补充
                        if not hasattr(candidate, 'interests'):
                            candidate.interests = []
                        candidate.interests.extend(aminer_result.get("interests", []))
                        
                        # 存储AMiner ID用于后续参考
                        if not hasattr(candidate, 'aminer_id'):
                            candidate.aminer_id = None
                        candidate.aminer_id = aminer_result.get("aminer_id")
                        
                        logger.info(f"[侦探节点] AMiner验证成功: {candidate.name} (置信度: {aminer_result.get('confidence_score', 0):.2f})")
                        aminer_enriched = True
                    else:
                        reason = aminer_result.get("reason", "unknown") if aminer_result else "api_error"
                        logger.debug(f"[侦探节点] AMiner未找到匹配或置信度低: {candidate.name} ({reason})")
                        
                except Exception as e:
                    logger.warning(f"[侦探节点] AMiner API异常: {str(e)}")
            
            # 步骤2: 使用DuckDuckGo搜索主页（AMiner成功或未启用时都需要搜索主页）
            search_results = search_scholar_homepage(candidate.name, candidate.affiliation)
            
            if search_results:
                # 查找最佳匹配URL
                best_url = find_best_homepage_url(search_results, candidate.name, candidate.affiliation)
                
                if best_url:
                    candidate.homepage = best_url
                    logger.info(f"[侦探节点] 找到URL: {best_url}")
                    # 如果找到主页，更新状态为继续处理
                    candidate.status = "PENDING"  # 等待审计节点处理
                else:
                    logger.warning(f"[侦探节点] 搜索结果中没有找到合适的URL")
                    candidate.status = "FAILED"
                    candidate.skip_reason = "搜索结果中未找到合适的主页"
            else:
                if aminer_enriched:
                    # 即使主页搜索失败，如果AMiner验证成功，仍然继续处理
                    logger.info(f"[侦探节点] DuckDuckGo搜索无结果，但AMiner验证成功，继续处理")
                    candidate.status = "PENDING"
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

