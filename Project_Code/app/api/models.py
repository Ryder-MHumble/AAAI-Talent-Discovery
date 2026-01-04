"""Pydantic models for API Request/Response schemas"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


# Request Models
class CheckPersonRequest(BaseModel):
    """Request model for single person verification"""
    name: str = Field(..., description="Full name of the scholar")
    affiliation: str = Field(..., description="Current affiliation/university")


class StartJobRequest(BaseModel):
    """Request model for batch job"""
    limit: Optional[int] = Field(None, description="Optional limit for testing (processes only N candidates)")


# Response Models
class CandidateProfile(BaseModel):
    """Core data model for a candidate"""
    name: str
    affiliation: str
    role: str  # e.g., "Invited Speaker", "Technical Track"
    status: Literal["PENDING", "SKIPPED", "VERIFIED", "FAILED"] = "PENDING"
    
    # Verification Results
    homepage: Optional[str] = None
    email: Optional[str] = None
    name_cn: Optional[str] = None
    bachelor_univ: Optional[str] = None
    
    # Processing Metadata
    skip_reason: Optional[str] = None
    verification_time: Optional[datetime] = None


class CheckPersonResponse(BaseModel):
    """Response for single person check"""
    name: str
    affiliation: str
    status: Literal["VERIFIED", "FAILED"]
    homepage: Optional[str] = None
    email: Optional[str] = None
    name_cn: Optional[str] = None
    bachelor_univ: Optional[str] = None
    message: Optional[str] = None


class StartJobResponse(BaseModel):
    """Response for job creation"""
    job_id: str
    message: str
    total_candidates: int
    started_at: datetime


class JobStatusResponse(BaseModel):
    """Response for job status query"""
    job_id: str
    status: Literal["RUNNING", "COMPLETED", "FAILED"]
    progress: int  # Number of candidates processed
    total: int
    verified_count: int
    failed_count: int
    skipped_count: int

