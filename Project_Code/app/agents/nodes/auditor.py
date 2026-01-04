"""审计节点 - 验证候选人主页并提取信息"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict

from app.agents.state import AgentState
from app.agents.tools.verify import check_url_connectivity, fetch_page_text, semantic_match, extract_email_simple
from app.core.llm import get_llm
from langchain.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


# LLM提示词用于档案提取
PROFILE_EXTRACTION_PROMPT = """你是一位专业的HR研究员。
我将提供一位学者主页的文本内容。
你必须将以下字段提取为JSON格式：

- `name_cn`: 中文姓名汉字（例如："张三"）。如果未找到则返回null。
- `email`: 电子邮箱地址。如果未找到则返回null。
- `bachelor_univ`: 他们获得学士/本科学位的大学。查找"B.S."、"B.E."、"Bachelor"、"Undergraduate"。如果未找到则返回null。
- `is_verified`: 布尔值。如果页面明确提到所属单位"{affiliation}"则为True。

输入姓名: {name}
输入所属单位: {affiliation}

页面内容:
{page_text}

仅返回包含这4个字段的有效JSON对象。不要额外的文本或解释。
"""


async def extract_profile_with_llm(
    page_text: str, 
    name: str, 
    affiliation: str
) -> Optional[Dict]:
    """
    使用LLM从主页文本中提取结构化信息
    
    Args:
        page_text: 主页的文本内容
        name: 候选人姓名
        affiliation: 预期所属单位
        
    Returns:
        包含提取字段的字典，如果提取失败则返回None
    """
    try:
        llm = get_llm()
        
        prompt = ChatPromptTemplate.from_template(PROFILE_EXTRACTION_PROMPT)
        chain = prompt | llm
        
        response = await chain.ainvoke({
            "name": name,
            "affiliation": affiliation,
            "page_text": page_text[:8000]  # 限制长度以避免token溢出
        })
        
        # 将LLM响应解析为JSON
        content = response.content
        
        # 尝试从响应中提取JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        extracted = json.loads(content.strip())
        
        logger.info(f"[审计节点] LLM提取结果: {extracted}")
        return extracted
        
    except Exception as e:
        logger.error(f"[审计节点] LLM提取失败: {str(e)}")
        return None


async def auditor_node(state: AgentState) -> AgentState:
    """
    节点4: 审计
    对有主页URL的候选人执行二元验证
    如果验证通过，使用LLM提取额外信息
    
    Args:
        state: 当前智能体状态
        
    Returns:
        包含验证结果的更新状态
    """
    candidates = state["candidates"]
    
    # 查找需要审计的候选人（有主页但尚未验证/失败）
    for idx, candidate in enumerate(candidates):
        if candidate.homepage and candidate.status == "PENDING":
            logger.info(f"[审计节点] 验证 #{idx}: {candidate.name} -> {candidate.homepage}")
            
            # 步骤1: 检查连接性
            is_accessible, status_code = await check_url_connectivity(candidate.homepage)
            
            if not is_accessible:
                logger.warning(f"[审计节点] URL不可访问 (状态码 {status_code})")
                candidate.status = "FAILED"
                candidate.skip_reason = f"主页不可访问 (HTTP {status_code})"
                candidate.verification_time = datetime.now()
                continue
            
            # 步骤2: 获取页面内容
            page_text = await fetch_page_text(candidate.homepage)
            
            if not page_text:
                logger.warning(f"[审计节点] 获取页面文本失败")
                candidate.status = "FAILED"
                candidate.skip_reason = "无法提取页面内容"
                candidate.verification_time = datetime.now()
                continue
            
            # 步骤3: 语义匹配
            is_match = semantic_match(page_text, candidate.name, candidate.affiliation)
            
            if not is_match:
                logger.warning(f"[审计节点] 页面内容与候选人不匹配")
                candidate.status = "FAILED"
                candidate.skip_reason = "页面内容与姓名/所属单位不匹配"
                candidate.verification_time = datetime.now()
                continue
            
            # 步骤4: 验证通过 - 使用LLM提取额外信息
            logger.info(f"[审计节点] ✓ 验证通过: {candidate.name}")
            candidate.status = "VERIFIED"
            
            # 首先提取简单邮箱（回退方案）
            candidate.email = extract_email_simple(page_text)
            
            # 使用LLM进行高级提取
            extracted = await extract_profile_with_llm(page_text, candidate.name, candidate.affiliation)
            
            if extracted:
                # 如果有LLM结果则覆盖
                if extracted.get('email'):
                    candidate.email = extracted['email']
                if extracted.get('name_cn'):
                    candidate.name_cn = extracted['name_cn']
                if extracted.get('bachelor_univ'):
                    candidate.bachelor_univ = extracted['bachelor_univ']
            
            candidate.verification_time = datetime.now()
            
            logger.info(f"[审计节点] 提取结果 - 邮箱: {candidate.email}, 中文名: {candidate.name_cn}, 本科院校: {candidate.bachelor_univ}")
    
    return state

