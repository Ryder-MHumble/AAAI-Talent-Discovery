"""FastAPI Route Definitions"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from datetime import datetime
import uuid
import logging
from typing import Dict

from app.api.models import (
    CheckPersonRequest, CheckPersonResponse,
    StartJobRequest, StartJobResponse,
    JobStatusResponse, CandidateProfile
)
from app.agents import create_agent_graph, AgentState
from app.services.excel_service import generate_excel_report, generate_full_report

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/v1", tags=["AAAI Talent Hunter"])

# In-memory storage for jobs (replace with database in production)
job_store: Dict[str, AgentState] = {}


@router.post("/check-person", response_model=CheckPersonResponse)
async def check_single_person(request: CheckPersonRequest):
    """
    On-demand verification of a single scholar.
    
    This endpoint spawns a mini-graph to check just one person immediately.
    
    Args:
        request: CheckPersonRequest with name and affiliation
        
    Returns:
        CheckPersonResponse with verification results
    """
    logger.info(f"[API] Single check request: {request.name} @ {request.affiliation}")
    
    try:
        # Create a mini-graph with just this one candidate
        graph = create_agent_graph()
        
        # Initial state with a single candidate
        initial_state: AgentState = {
            "job_id": f"single-{uuid.uuid4().hex[:8]}",
            "candidates": [
                CandidateProfile(
                    name=request.name,
                    affiliation=request.affiliation,
                    role="API Check",
                    status="PENDING"
                )
            ],
            "current_index": 0,
            "is_complete": False,
            "error_message": ""
        }
        
        # Note: Since we're checking a single person, we skip ingestion
        # and go directly to detective and auditor
        from app.agents.nodes.detective import detective_node
        from app.agents.nodes.auditor import auditor_node
        
        # Execute detective and auditor nodes
        state = await detective_node(initial_state)
        state = await auditor_node(state)
        
        candidate = state["candidates"][0]
        
        if candidate.status == "VERIFIED":
            return CheckPersonResponse(
                name=candidate.name,
                affiliation=candidate.affiliation,
                status="VERIFIED",
                homepage=candidate.homepage,
                email=candidate.email,
                name_cn=candidate.name_cn,
                bachelor_univ=candidate.bachelor_univ,
                message="Successfully verified"
            )
        else:
            return CheckPersonResponse(
                name=candidate.name,
                affiliation=candidate.affiliation,
                status="FAILED",
                message=candidate.skip_reason or "Verification failed"
            )
            
    except Exception as e:
        logger.error(f"[API] Single check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


async def run_batch_job(job_id: str, limit: int = None):
    """
    Background task to run the full agent workflow.
    
    Args:
        job_id: Unique job identifier
        limit: Optional limit on number of candidates to process
    """
    logger.info(f"[BackgroundJob] Starting job {job_id}")
    
    try:
        graph = create_agent_graph()
        
        initial_state: AgentState = {
            "job_id": job_id,
            "candidates": [],
            "current_index": 0,
            "is_complete": False,
            "error_message": ""
        }
        
        # Run the full workflow
        final_state = await graph.ainvoke(initial_state)
        
        # Apply limit if specified (for testing)
        if limit:
            final_state["candidates"] = final_state["candidates"][:limit]
        
        # Store results
        job_store[job_id] = final_state
        
        logger.info(f"[BackgroundJob] Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"[BackgroundJob] Job {job_id} failed: {str(e)}")
        # Store error state
        job_store[job_id] = {
            "job_id": job_id,
            "candidates": [],
            "current_index": 0,
            "is_complete": False,
            "error_message": str(e)
        }


@router.post("/jobs/aaai-full-scan", response_model=StartJobResponse)
async def start_batch_job(request: StartJobRequest, background_tasks: BackgroundTasks):
    """
    Trigger a batch scraping job for all AAAI-26 candidates.
    
    The job runs in the background and results can be retrieved later.
    
    Args:
        request: StartJobRequest with optional limit
        background_tasks: FastAPI background tasks
        
    Returns:
        StartJobResponse with job_id
    """
    job_id = f"job-{uuid.uuid4().hex[:12]}"
    
    logger.info(f"[API] Starting batch job {job_id} (limit={request.limit})")
    
    # Add to background tasks
    background_tasks.add_task(run_batch_job, job_id, request.limit)
    
    return StartJobResponse(
        job_id=job_id,
        message="Job started successfully",
        total_candidates=0,  # Will be populated after ingestion
        started_at=datetime.now()
    )


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the current status of a batch job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        JobStatusResponse with current progress
    """
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    state = job_store[job_id]
    candidates = state["candidates"]
    
    return JobStatusResponse(
        job_id=job_id,
        status="COMPLETED" if state["is_complete"] else "RUNNING",
        progress=state["current_index"],
        total=len(candidates),
        verified_count=len([c for c in candidates if c.status == "VERIFIED"]),
        failed_count=len([c for c in candidates if c.status == "FAILED"]),
        skipped_count=len([c for c in candidates if c.status == "SKIPPED"])
    )


@router.get("/jobs/{job_id}/export")
async def export_job_results(job_id: str, format: str = "verified"):
    """
    Export job results as an Excel file.
    
    Args:
        job_id: Job identifier
        format: "verified" (only verified candidates) or "full" (all candidates)
        
    Returns:
        Excel file as streaming response
    """
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    state = job_store[job_id]
    candidates = state["candidates"]
    
    logger.info(f"[API] Exporting results for job {job_id} (format={format})")
    
    if format == "full":
        buffer = generate_full_report(candidates, job_id)
        filename = f"aaai_talent_full_{job_id}.xlsx"
    else:
        buffer = generate_excel_report(candidates, job_id)
        filename = f"aaai_talent_verified_{job_id}.xlsx"
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AAAI Talent Hunter",
        "version": "1.0.0"
    }

