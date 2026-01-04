"""FastAPI路由定义"""

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

# 路由器
router = APIRouter(prefix="/api/v1", tags=["AAAI Talent Hunter"])

# 任务的内存存储（生产环境需替换为数据库）
job_store: Dict[str, AgentState] = {}


@router.post("/check-person", response_model=CheckPersonResponse)
async def check_single_person(request: CheckPersonRequest):
    """
    单个学者的按需验证
    
    此端点创建一个迷你图来立即检查一个人
    
    Args:
        request: 包含姓名和单位的CheckPersonRequest
        
    Returns:
        包含验证结果的CheckPersonResponse
    """
    logger.info(f"[API] 单人检查请求: {request.name} @ {request.affiliation}")
    
    try:
        # 为单个候选人创建迷你图
        graph = create_agent_graph()
        
        # 单个候选人的初始状态
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
        
        # 注意：因为是检查单个人，跳过采集步骤，直接进入detective和auditor
        from app.agents.nodes.detective import detective_node
        from app.agents.nodes.auditor import auditor_node
        
        # 执行detective和auditor节点
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
    运行完整智能体工作流的后台任务
    
    Args:
        job_id: 唯一任务标识符
        limit: 可选的候选人处理数量限制
    """
    logger.info(f"[后台任务] 启动任务 {job_id}")
    
    try:
        graph = create_agent_graph()
        
        initial_state: AgentState = {
            "job_id": job_id,
            "candidates": [],
            "current_index": 0,
            "is_complete": False,
            "error_message": ""
        }
        
        # 运行完整工作流
        final_state = await graph.ainvoke(initial_state)
        
        # 如果指定了限制则应用（用于测试）
        if limit:
            final_state["candidates"] = final_state["candidates"][:limit]
        
        # 存储结果
        job_store[job_id] = final_state
        
        logger.info(f"[后台任务] 任务 {job_id} 成功完成")
        
    except Exception as e:
        logger.error(f"[后台任务] 任务 {job_id} 失败: {str(e)}")
        # 存储错误状态
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
    触发批量抓取所有AAAI-26候选人的任务
    
    任务在后台运行，结果稍后可检索
    
    Args:
        request: 带可选限制的StartJobRequest
        background_tasks: FastAPI后台任务
        
    Returns:
        包含job_id的StartJobResponse
    """
    job_id = f"job-{uuid.uuid4().hex[:12]}"
    
    logger.info(f"[API] 启动批量任务 {job_id} (limit={request.limit})")
    
    # 添加到后台任务
    background_tasks.add_task(run_batch_job, job_id, request.limit)
    
    return StartJobResponse(
        job_id=job_id,
        message="任务启动成功",
        total_candidates=0,  # 采集后填充
        started_at=datetime.now()
    )


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    获取批量任务的当前状态
    
    Args:
        job_id: 任务标识符
        
    Returns:
        包含当前进度的JobStatusResponse
    """
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail=f"任务 {job_id} 未找到")
    
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
    将任务结果导出为Excel文件
    
    Args:
        job_id: 任务标识符
        format: "verified"（仅验证通过的候选人）或"full"（所有候选人）
        
    Returns:
        流式响应的Excel文件
    """
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail=f"任务 {job_id} 未找到")
    
    state = job_store[job_id]
    candidates = state["candidates"]
    
    logger.info(f"[API] 导出任务 {job_id} 的结果 (format={format})")
    
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
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "AAAI 人才猎手",
        "version": "1.0.0"
    }

