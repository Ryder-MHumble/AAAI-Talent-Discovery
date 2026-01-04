"""LangGraph State Definitions"""

from typing import TypedDict, List, Literal
from app.api.models import CandidateProfile


class AgentState(TypedDict):
    """
    Shared state for the agent workflow.
    
    This state is passed between all nodes in the LangGraph.
    """
    job_id: str
    candidates: List[CandidateProfile]  # The main list of all candidates
    current_index: int  # Processing pointer for the current candidate
    is_complete: bool  # Flag indicating if all processing is done
    error_message: str  # Optional error tracking

