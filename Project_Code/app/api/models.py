"""API请求/响应的Pydantic模型"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


# 请求模型
class CheckPersonRequest(BaseModel):
    """单人验证的请求模型"""
    name: str = Field(..., description="学者的全名")
    affiliation: str = Field(..., description="当前所属单位/大学")


class StartJobRequest(BaseModel):
    """批量任务的请求模型"""
    limit: Optional[int] = Field(None, description="可选的测试限制（仅处理N个候选人）")


# 响应模型
class CandidateProfile(BaseModel):
    """候选人的核心数据模型"""
    name: str
    affiliation: str
    role: str  # 例如："受邀演讲者"、"技术轨道"
    status: Literal["PENDING", "SKIPPED", "VERIFIED", "FAILED"] = "PENDING"
    
    # 验证结果
    homepage: Optional[str] = None
    email: Optional[str] = None
    name_cn: Optional[str] = None
    bachelor_univ: Optional[str] = None
    
    # 处理元数据
    skip_reason: Optional[str] = None
    verification_time: Optional[datetime] = None


class CheckPersonResponse(BaseModel):
    """单人检查的响应"""
    name: str
    affiliation: str
    status: Literal["VERIFIED", "FAILED"]
    homepage: Optional[str] = None
    email: Optional[str] = None
    name_cn: Optional[str] = None
    bachelor_univ: Optional[str] = None
    message: Optional[str] = None


class StartJobResponse(BaseModel):
    """任务创建的响应"""
    job_id: str
    message: str
    total_candidates: int
    started_at: datetime


class JobStatusResponse(BaseModel):
    """任务状态查询的响应"""
    job_id: str
    status: Literal["RUNNING", "COMPLETED", "FAILED"]
    progress: int  # 已处理的候选人数量
    total: int
    verified_count: int
    failed_count: int
    skipped_count: int

