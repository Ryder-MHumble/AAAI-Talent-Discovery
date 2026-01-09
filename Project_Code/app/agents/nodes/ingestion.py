"""采集节点 - 获取并解析AAAI-26候选人数据"""

import httpx
from bs4 import BeautifulSoup
from typing import List
import logging

from app.agents.state import AgentState
from app.api.models import CandidateProfile
from app.core.config import settings
from app.agents.tools.aaai_scraper import scrape_all_aaai_sources

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
    
    此函数已弃用 - 请使用 app.agents.tools.aaai_scraper 中的专用函数
    保留用于向后兼容性。
    
    Args:
        url: AAAI页面URL
        
    Returns:
        CandidateProfile对象列表
    """
    # 转发到新的爬虫工具
    logger.warning("[采集节点] scrape_aaai_page已弃用，请使用aaai_scraper.py中的专用函数")
    return []


async def ingestion_node(state: AgentState) -> AgentState:
    """
    节点1: 采集
    获取AAAI-26数据并填充候选人列表
    
    支持的数据来源：
    1. Invited Speakers - 特邀演讲者
    2. Bridge Program - Bridge Committee成员
    3. Tutorials and Labs - 讲师和指导员
    4. Workshops - Workshop组织者
    
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
        # 生产环境抓取真实AAAI页面（多个来源）
        logger.info("[采集节点] 从多个AAAI页面源抓取数据 (PROD模式)")
        
        try:
            candidates = await scrape_all_aaai_sources(
                invited_speakers_url=settings.AAAI_INVITED_SPEAKERS_URL,
                bridge_program_url=settings.BRIDGE_PROGRAM_URL,
                tutorials_url=settings.TUTORIALS_LABS_URL,
                workshops_url=settings.WORKSHOPS_URL
            )
        except Exception as e:
            logger.error(f"[采集节点] 从AAAI页面抓取数据失败: {str(e)}")
            # 降级到模拟数据
            logger.warning("[采集节点] 降级到模拟数据")
            candidates = MOCK_CANDIDATES.copy()
    
    state["candidates"] = candidates
    state["current_index"] = 0
    state["is_complete"] = False
    
    logger.info(f"[采集节点] 已加载{len(candidates)}位候选人")
    
    return state

