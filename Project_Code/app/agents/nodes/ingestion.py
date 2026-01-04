"""采集节点 - 获取并解析AAAI-26候选人数据"""

import httpx
from bs4 import BeautifulSoup
from typing import List
import logging

from app.agents.state import AgentState
from app.api.models import CandidateProfile
from app.core.config import settings

logger = logging.getLogger(__name__)


# 开发环境的模拟数据
MOCK_CANDIDATES = [
    CandidateProfile(
        name="Haoyang Li",
        affiliation="Carnegie Mellon University",
        role="Invited Speaker",
        status="PENDING"
    ),
    CandidateProfile(
        name="Yi Wu",
        affiliation="Google DeepMind",
        role="Technical Track",
        status="PENDING"
    ),
    CandidateProfile(
        name="Jie Tang",
        affiliation="Tsinghua University",
        role="Invited Speaker",
        status="PENDING"
    ),
    CandidateProfile(
        name="Xiaojun Chang",
        affiliation="University of Sydney",
        role="Technical Track",
        status="PENDING"
    ),
    CandidateProfile(
        name="Lei Chen",
        affiliation="Hong Kong University of Science and Technology",
        role="Invited Speaker",
        status="PENDING"
    ),
]


async def scrape_aaai_page(url: str) -> List[CandidateProfile]:
    """
    抓取AAAI网站以提取候选人信息
    
    Args:
        url: AAAI页面URL
        
    Returns:
        CandidateProfile对象列表
    """
    candidates = []
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                logger.error(f"获取{url}失败: {response.status_code}")
                return candidates
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 这是一个占位解析器 - 实际实现取决于AAAI的HTML结构
            # 查找常见模式如:
            # - <h3>或<h4>标签用于姓名
            # - 相邻的<p>或<span>用于所属单位
            
            # 示例解析逻辑（根据实际HTML结构调整）
            for item in soup.find_all(['div', 'li'], class_=['speaker', 'author', 'participant']):
                name = None
                affiliation = None
                
                # 尝试提取姓名
                name_tag = item.find(['h3', 'h4', 'strong', 'b'])
                if name_tag:
                    name = name_tag.get_text(strip=True)
                
                # 尝试提取所属单位
                aff_tag = item.find(['p', 'span', 'em'], class_=['affiliation', 'institution'])
                if aff_tag:
                    affiliation = aff_tag.get_text(strip=True)
                
                if name and affiliation:
                    candidates.append(CandidateProfile(
                        name=name,
                        affiliation=affiliation,
                        role="受邀演讲者" if "invited" in url.lower() else "技术轨道",
                        status="PENDING"
                    ))
        
        logger.info(f"从{url}抓取了{len(candidates)}位候选人")
        
    except Exception as e:
        logger.error(f"抓取{url}时出错: {str(e)}")
    
    return candidates


async def ingestion_node(state: AgentState) -> AgentState:
    """
    节点1: 采集
    获取AAAI-26数据并填充候选人列表
    
    Args:
        state: 当前智能体状态
        
    Returns:
        已填充候选人的更新状态
    """
    logger.info(f"[采集节点] 开始处理 job_id={state['job_id']}")
    
    candidates = []
    
    if settings.APP_ENV == "DEV":
        # 开发环境使用模拟数据
        logger.info("[采集节点] 使用模拟数据 (DEV模式)")
        candidates = MOCK_CANDIDATES.copy()
    else:
        # 生产环境抓取真实AAAI页面
        logger.info("[采集节点] 抓取AAAI页面 (PROD模式)")
        
        invited_speakers = await scrape_aaai_page(settings.AAAI_INVITED_SPEAKERS_URL)
        technical_track = await scrape_aaai_page(settings.AAAI_TECHNICAL_TRACK_URL)
        
        candidates = invited_speakers + technical_track
    
    state["candidates"] = candidates
    state["current_index"] = 0
    state["is_complete"] = False
    
    logger.info(f"[采集节点] 已加载{len(candidates)}位候选人")
    
    return state

