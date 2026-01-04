"""FastAPI应用程序入口"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys

from app.api.endpoints import router
from app.core.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="AAAI-26 人才猎手",
    description="面向服务的多智能体系统，用于识别海外华人学者",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS中间件（生产环境需调整origins）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """应用启动任务"""
    logger.info("=" * 80)
    logger.info("AAAI-26 人才猎手 - 服务启动中")
    logger.info("=" * 80)
    logger.info(f"环境: {settings.APP_ENV}")
    logger.info(f"LLM模型: {settings.SILICONFLOW_MODEL}")
    logger.info(f"并发搜索数: {settings.CONCURRENT_SEARCHES}")
    logger.info("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭任务"""
    logger.info("AAAI-26 人才猎手 - 服务关闭中")


@app.get("/")
async def root():
    """根端点"""
    return {
        "service": "AAAI-26 人才猎手",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.APP_ENV == "DEV" else False,
        log_level="info"
    )

