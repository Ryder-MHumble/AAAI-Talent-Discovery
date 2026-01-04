"""FastAPI Application Entry Point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys

from app.api.endpoints import router
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AAAI-26 Talent Hunter",
    description="Service-Oriented Multi-Agent System for identifying Overseas Chinese Scholars",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (adjust origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("=" * 80)
    logger.info("AAAI-26 Talent Hunter - Service Starting")
    logger.info("=" * 80)
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"LLM Model: {settings.SILICONFLOW_MODEL}")
    logger.info(f"Concurrent Searches: {settings.CONCURRENT_SEARCHES}")
    logger.info("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("AAAI-26 Talent Hunter - Service Shutting Down")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AAAI-26 Talent Hunter",
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

