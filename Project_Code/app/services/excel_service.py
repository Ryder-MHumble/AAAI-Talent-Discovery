"""Excel导出服务"""

import pandas as pd
from typing import List
from io import BytesIO
import logging

from app.api.models import CandidateProfile

logger = logging.getLogger(__name__)


def generate_excel_report(candidates: List[CandidateProfile], job_id: str) -> BytesIO:
    """
    从候选人结果生成Excel文件
    
    Args:
        candidates: CandidateProfile对象列表
        job_id: 任务标识符
        
    Returns:
        包含Excel文件的BytesIO缓冲区
    """
    # 仅筛选验证通过的候选人
    verified = [c for c in candidates if c.status == "VERIFIED"]
    
    logger.info(f"[Excel服务] 为{len(verified)}位验证通过的候选人生成报告")
    
    # 为DataFrame准备数据
    data = []
    for candidate in verified:
        data.append({
            "姓名": candidate.name,
            "中文姓名": candidate.name_cn or "无",
            "当前单位": candidate.affiliation,
            "角色": candidate.role,
            "主页": candidate.homepage or "无",
            "邮箱": candidate.email or "无",
            "本科院校": candidate.bachelor_univ or "无",
            "验证时间": candidate.verification_time.strftime("%Y-%m-%d %H:%M:%S") if candidate.verification_time else "无"
        })
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 在内存中创建Excel文件
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='已验证学者', index=False)
        
        # 添加汇总表
        summary_data = {
            "指标": [
                "任务ID",
                "总候选人数",
                "已验证",
                "失败",
                "跳过",
                "生成时间"
            ],
            "值": [
                job_id,
                len(candidates),
                len([c for c in candidates if c.status == "VERIFIED"]),
                len([c for c in candidates if c.status == "FAILED"]),
                len([c for c in candidates if c.status == "SKIPPED"]),
                pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='汇总', index=False)
    
    buffer.seek(0)
    
    logger.info(f"[Excel服务] Excel报告生成成功")
    
    return buffer


def generate_full_report(candidates: List[CandidateProfile], job_id: str) -> BytesIO:
    """
    生成包含所有候选人（所有状态）的完整Excel文件
    
    Args:
        candidates: CandidateProfile对象列表
        job_id: 任务标识符
        
    Returns:
        包含Excel文件的BytesIO缓冲区
    """
    logger.info(f"[Excel服务] 为{len(candidates)}位候选人生成完整报告")
    
    # 为DataFrame准备数据
    data = []
    for candidate in candidates:
        data.append({
            "姓名": candidate.name,
            "中文姓名": candidate.name_cn or "",
            "单位": candidate.affiliation,
            "角色": candidate.role,
            "状态": candidate.status,
            "主页": candidate.homepage or "",
            "邮箱": candidate.email or "",
            "本科院校": candidate.bachelor_univ or "",
            "跳过原因": candidate.skip_reason or "",
            "验证时间": candidate.verification_time.strftime("%Y-%m-%d %H:%M:%S") if candidate.verification_time else ""
        })
    
    df = pd.DataFrame(data)
    
    # 创建Excel文件
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='所有候选人', index=False)
    
    buffer.seek(0)
    
    return buffer

