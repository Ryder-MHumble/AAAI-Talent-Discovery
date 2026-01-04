"""LangGraph状态定义"""

from typing import TypedDict, List, Literal
from app.api.models import CandidateProfile


class AgentState(TypedDict):
    """
    智能体工作流的共享状态
    
    此状态在LangGraph的所有节点之间传递
    """
    job_id: str
    candidates: List[CandidateProfile]  # 所有候选人的主列表
    current_index: int  # 当前候选人的处理指针
    is_complete: bool  # 标志所有处理是否完成
    error_message: str  # 可选的错误跟踪

