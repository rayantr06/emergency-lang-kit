"""
ELK API Server
Gateway for Emergency Call Analysis.
Async-first architecture: Submits jobs to Redis/Arq workers.
"""

import logging
import asyncio
from sqlalchemy import text
from fastapi import FastAPI, UploadFile, File, HTTPException
from elk.api.schemas import HealthResponse, ProcessResponse, TranscribeRequest
from elk.api.middleware import setup_production_middleware
from elk.api.routes import router as job_router
from elk.database.db import init_db, async_engine
from elk.core.config import settings
from elk.api.auth import APIKeyMiddleware
from arq import create_pool
from arq.connections import RedisSettings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise AI Agent for Emergency Call Analysis (Async Architecture)",
    version=settings.VERSION
)

# Apply production middleware
setup_production_middleware(app)
app.add_middleware(APIKeyMiddleware)

# Mount Routes
app.include_router(job_router, tags=["Async Jobs"])

@app.on_event("startup")
async def startup_event():
    """Initialize resources (DB, Redis connection)."""
    logger.info(f"Initializing {settings.APP_NAME}...")
    await init_db()
    # Cache Redis pool globally on app state for performance
    app.state.redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    logger.info("ELK API Ready.")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources."""
    if hasattr(app.state, "redis"):
        await app.state.redis.close()
    logger.info("ELK API Shutdown.")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed System Health Check."""
    import psutil

    # Simple system stats
    system_stats = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent
    }

    dependencies = {}
    try:
        redis = getattr(app.state, "redis", None)
        if redis:
            await asyncio.wait_for(redis.ping(), timeout=settings.QUEUE_OP_TIMEOUT)
            queue_depth = await asyncio.wait_for(redis.llen("arq:queue"), timeout=settings.QUEUE_OP_TIMEOUT)
            dependencies["redis"] = f"up (queue_depth={queue_depth})"
        else:
            dependencies["redis"] = "unavailable"
    except Exception:
        dependencies["redis"] = "down"

    try:
        async with async_engine.connect() as conn:
            await asyncio.wait_for(conn.execute(text("SELECT 1")), timeout=settings.QUEUE_OP_TIMEOUT)
        dependencies["database"] = "up"
    except Exception:
        dependencies["database"] = "down"
    
    # API Gateway doesn't manage models or cache - workers do
    
    return HealthResponse(
        status="healthy",
        active_packs=["dz-kab-protection"],
        system_load=system_stats,
        gpu_status={"role": "api-gateway", "available": False}, 
        loaded_models={"count": 0, "role": "api-gateway"},
        cache_stats={"role": "api-gateway"},
        dependencies=dependencies
    )

# Legacy Endpoint Wrapper (Optional compatibility)
@app.post("/v1/process", response_model=ProcessResponse, deprecated=True)
async def process_call_legacy(request: TranscribeRequest):
    """
    DEPRECATED: Use POST /jobs for async processing.
    This endpoint is now a wrapper that blocks until job completion (not recommended).
    """
    raise HTTPException(
        status_code=410, 
        detail="Synchronous processing is deprecated. Please use POST /jobs."
    )
