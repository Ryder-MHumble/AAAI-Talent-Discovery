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
    
    导出字段（按用户需求）：
    - 英文姓名
    - 中文姓名
    - 单位
    - 单位所属国家/地区
    - 职位
    - 研究方向
    - 个人主页
    - 邮箱
    
    Args:
        candidates: CandidateProfile对象列表
        job_id: 任务标识符
        
    Returns:
        包含Excel文件的BytesIO缓冲区
    """
    # 仅筛选验证通过的候选人
    verified = [c for c in candidates if c.status == "VERIFIED"]
    
    logger.info(f"[Excel服务] 为{len(verified)}位验证通过的候选人生成报告")
    
    # 为DataFrame准备数据 - 按照用户指定的字段顺序
    data = []
    for candidate in verified:
        # 整理研究方向（从interests或research_interests）
        interests = []
        if hasattr(candidate, 'interests') and candidate.interests:
            interests.extend(candidate.interests)
        if hasattr(candidate, 'research_interests') and candidate.research_interests:
            interests.extend(candidate.research_interests)
        interests_str = "; ".join(set(interests)) if interests else "无"
        
        data.append({
            "英文姓名": candidate.name,
            "中文姓名": candidate.name_cn or "无",
            "单位": candidate.affiliation,
            "单位所属国家/地区": candidate.country_region or "无",
            "职位": candidate.position or candidate.role or "无",
            "研究方向": interests_str,
            "个人主页": candidate.homepage or "无",
            "邮箱": candidate.email or "无"
        })
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 确保列的顺序与上述字段顺序一致
    column_order = ["英文姓名", "中文姓名", "单位", "单位所属国家/地区", "职位", "研究方向", "个人主页", "邮箱"]
    df = df[column_order]
    
    # 在内存中创建Excel文件
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='已验证学者', index=False)
        
        # 调整列宽以提高可读性
        from openpyxl.utils import get_column_letter
        worksheet = writer.sheets['已验证学者']
        
        # 设置列宽
        column_widths = {
            "英文姓名": 20,
            "中文姓名": 15,
            "单位": 30,
            "单位所属国家/地区": 18,
            "职位": 20,
            "研究方向": 35,
            "个人主页": 40,
            "邮箱": 25
        }
        
        for idx, col in enumerate(column_order, 1):
            worksheet.column_dimensions[get_column_letter(idx)].width = column_widths.get(col, 15)
        
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
    
    logger.info(f"[Excel服务] Excel报告生成成功，包含{len(verified)}条记录")
    
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

