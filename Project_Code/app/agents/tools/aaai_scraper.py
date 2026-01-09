"""AAAI-26页面数据提取工具"""

import httpx
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from app.api.models import CandidateProfile

logger = logging.getLogger(__name__)


async def scrape_invited_speakers(url: str) -> List[CandidateProfile]:
    """
    从Invited Speakers页面提取讲者信息
    
    目标元素：div class="wp-block-columns is-layout-flex wp-container-core-columns-is-layout-9d6595d7 wp-block-columns-is-layout-flex"
    
    Args:
        url: https://aaai.org/conference/aaai/aaai-26/invited-speakers/
        
    Returns:
        CandidateProfile列表
    """
    candidates = []
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                logger.error(f"获取{url}失败: {response.status_code}")
                return candidates
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找目标容器
            target_div = soup.find('div', class_='wp-block-columns')
            
            if not target_div:
                logger.warning("未找到目标div容器")
                return candidates
            
            # 提取讲者信息
            # 通常讲者信息在<h3>或<strong>标签中，机构在相邻的<p>或<em>中
            for section in target_div.find_all(['section', 'div'], class_=['wp-block-column']):
                name = None
                affiliation = None
                
                # 尝试提取姓名
                name_tag = section.find(['h3', 'h4', 'strong'])
                if name_tag:
                    name = name_tag.get_text(strip=True)
                
                # 尝试提取机构
                aff_tag = section.find(['p', 'em'])
                if aff_tag:
                    affiliation = aff_tag.get_text(strip=True)
                
                if name and affiliation:
                    candidates.append(CandidateProfile(
                        name=name,
                        affiliation=affiliation,
                        role="Invited Speaker",
                        status="PENDING"
                    ))
                    logger.info(f"找到讲者: {name} ({affiliation})")
        
        logger.info(f"从Invited Speakers页面提取了{len(candidates)}名讲者")
        
    except Exception as e:
        logger.error(f"Invited Speakers页面提取异常: {str(e)}")
    
    return candidates


async def scrape_bridge_committee(url: str) -> List[CandidateProfile]:
    """
    从Bridge Program页面提取Bridge Committee成员信息
    
    Args:
        url: https://aaai.org/conference/aaai/aaai-26/bridge-program/
        
    Returns:
        CandidateProfile列表
    """
    candidates = []
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                logger.error(f"获取{url}失败: {response.status_code}")
                return candidates
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找"Bridge Committee"标题之后的内容
            for heading in soup.find_all(['h2', 'h3']):
                if 'bridge committee' in heading.get_text(strip=True).lower():
                    # 查找该标题后的内容
                    section = heading.find_next(['div', 'ul', 'ol'])
                    
                    if section:
                        # 提取列表项中的人员信息
                        for item in section.find_all('li'):
                            text = item.get_text(strip=True)
                            # 假设格式为"名字 - 机构"或类似
                            if '-' in text:
                                parts = text.split('-')
                                name = parts[0].strip()
                                affiliation = parts[1].strip() if len(parts) > 1 else "Unknown"
                                
                                candidates.append(CandidateProfile(
                                    name=name,
                                    affiliation=affiliation,
                                    role="Bridge Committee",
                                    status="PENDING"
                                ))
                                logger.info(f"找到Bridge Committee成员: {name}")
        
        logger.info(f"从Bridge Program页面提取了{len(candidates)}名成员")
        
    except Exception as e:
        logger.error(f"Bridge Committee页面提取异常: {str(e)}")
    
    return candidates


async def scrape_tutorials_and_labs(url: str) -> List[CandidateProfile]:
    """
    从Tutorial and Lab Forum页面提取讲师信息
    
    目标格式：「# Half Day Tutorials # TH01: A Decade of Sparse Training: Why Do We Still Stick to Dense Training?」下的人员
    
    Args:
        url: https://aaai.org/conference/aaai/aaai-26/tutorials-and-labs/
        
    Returns:
        CandidateProfile列表
    """
    candidates = []
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                logger.error(f"获取{url}失败: {response.status_code}")
                return candidates
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找所有Tutorial部分
            for heading in soup.find_all(['h2', 'h3', 'h4']):
                heading_text = heading.get_text(strip=True).lower()
                
                # 查找包含"tutorial"或"half day"的标题
                if 'tutorial' in heading_text or 'half day' in heading_text:
                    # 查找标题下的内容
                    section = heading.find_next(['div', 'table', 'ul'])
                    
                    if section:
                        # 在section中查找人员信息
                        # 通常在<strong>, <b>, 或单独的行中
                        for person_tag in section.find_all(['strong', 'b', 'span']):
                            name = person_tag.get_text(strip=True)
                            
                            # 简单的名字过滤：英文名字通常有2-4个单词
                            if name and len(name.split()) <= 4 and name.strip():
                                # 尝试从相邻元素获取机构信息
                                parent = person_tag.find_parent('li') or person_tag.find_parent('tr')
                                affiliation = "Unknown"
                                
                                if parent:
                                    affiliation_tag = parent.find(['em', 'span', 'td'])
                                    if affiliation_tag and affiliation_tag != person_tag:
                                        affiliation = affiliation_tag.get_text(strip=True)
                                
                                candidates.append(CandidateProfile(
                                    name=name,
                                    affiliation=affiliation,
                                    role="Tutorial Instructor",
                                    status="PENDING"
                                ))
                                logger.info(f"找到讲师: {name}")
        
        logger.info(f"从Tutorials and Labs页面提取了{len(candidates)}名讲师")
        
    except Exception as e:
        logger.error(f"Tutorials and Labs页面提取异常: {str(e)}")
    
    return candidates


async def scrape_workshops_organization(url: str) -> List[CandidateProfile]:
    """
    从Workshops页面提取Organization Committee成员信息
    
    Args:
        url: https://aaai.org/conference/aaai/aaai-26/workshops/
        
    Returns:
        CandidateProfile列表
    """
    candidates = []
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                logger.error(f"获取{url}失败: {response.status_code}")
                return candidates
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找Workshop列表
            for workshop_section in soup.find_all(['div', 'section'], class_=['workshop', 'ws-item']):
                # 查找Organization Committee或类似的标题
                for heading in workshop_section.find_all(['h3', 'h4', 'h5']):
                    if 'organization' in heading.get_text(strip=True).lower():
                        # 查找该标题下的成员列表
                        org_section = heading.find_next(['ul', 'ol', 'div'])
                        
                        if org_section:
                            for item in org_section.find_all('li'):
                                text = item.get_text(strip=True)
                                
                                # 解析格式："名字 (机构)"或"名字 - 机构"
                                name = text
                                affiliation = "Unknown"
                                
                                if '(' in text and ')' in text:
                                    name = text[:text.index('(')].strip()
                                    affiliation = text[text.index('(')+1:text.index(')')].strip()
                                elif '-' in text:
                                    parts = text.split('-')
                                    name = parts[0].strip()
                                    affiliation = parts[1].strip() if len(parts) > 1 else affiliation
                                
                                if name:
                                    candidates.append(CandidateProfile(
                                        name=name,
                                        affiliation=affiliation,
                                        role="Workshop Organizer",
                                        status="PENDING"
                                    ))
                                    logger.info(f"找到Workshop组织者: {name}")
        
        logger.info(f"从Workshops页面提取了{len(candidates)}名组织者")
        
    except Exception as e:
        logger.error(f"Workshops页面提取异常: {str(e)}")
    
    return candidates


async def scrape_all_aaai_sources(
    invited_speakers_url: str,
    bridge_program_url: str,
    tutorials_url: str,
    workshops_url: str
) -> List[CandidateProfile]:
    """
    从所有AAAI-26来源汇总提取候选人
    
    Args:
        invited_speakers_url: Invited Speakers页面URL
        bridge_program_url: Bridge Program页面URL
        tutorials_url: Tutorials and Labs页面URL
        workshops_url: Workshops页面URL
        
    Returns:
        所有候选人的合并列表
    """
    all_candidates = []
    
    logger.info("[AAAI数据提取] 开始从多个来源提取候选人数据...")
    
    # 并行提取所有来源
    invited = await scrape_invited_speakers(invited_speakers_url)
    bridge = await scrape_bridge_committee(bridge_program_url)
    tutorials = await scrape_tutorials_and_labs(tutorials_url)
    workshops = await scrape_workshops_organization(workshops_url)
    
    # 合并结果
    all_candidates.extend(invited)
    all_candidates.extend(bridge)
    all_candidates.extend(tutorials)
    all_candidates.extend(workshops)
    
    # 去重：基于名字和机构组合
    seen = set()
    unique_candidates = []
    
    for candidate in all_candidates:
        key = (candidate.name.lower(), candidate.affiliation.lower())
        if key not in seen:
            seen.add(key)
            unique_candidates.append(candidate)
    
    logger.info(f"[AAAI数据提取] 汇总提取了{len(unique_candidates)}名唯一候选人")
    
    return unique_candidates
