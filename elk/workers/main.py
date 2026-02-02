"""
ELK Async Worker
Handles background processing of emergency calls using Arq and Redis.
Executes the pipeline and updates Job state in the database.
"""

import sys
import os
import asyncio
import logging
import traceback
from datetime import datetime
from typing import Dict, Any

from arq import Worker
from arq.connections import RedisSettings

from elk.database.db import get_session, async_engine, init_db
from elk.database.models import Job, JobStatus
from elk.factory.loader import load_pipeline
from elk.engine.models import get_model_registry
from elk.connectors.factory import ConnectorFactory
from elk.core.config import settings

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# REDIS_URL and connection logic managed by Arq WorkerSettings

# Settings
REDIS_SETTINGS = RedisSettings.from_dsn(settings.REDIS_URL)

async def startup(ctx):
    """Worker startup: Init DB and Load Models."""
    logger.info("Worker starting up...")
    
    # Initialize DB tables if needed
    await init_db()
    
    # Warm up models (Singleton)
    # This ensures the first job doesn't suffer latency
    registry = get_model_registry()
    try:
        # Load default pack pipeline configuration to trigger pre-loading
        # In a real multi-tenant setup, we might load dynamically or have "hot" models
        # For now, we optimize for the Kabyle pack
        pipeline = load_pipeline("dz-kab-protection", {"whisper_model": "small"})
        logger.info("Models warmed up successfully.")
    except Exception as e:
        logger.error(f"Model warmup failed: {e}")

async def shutdown(ctx):
    """Worker shutdown: Cleanup."""
    logger.info("Worker shutting down...")
    get_model_registry().unload_all()

async def process_audio_job(ctx, job_id: str, pack_name: str, audio_path: str, meta: Dict[str, Any]):
    """
    Core Task: Execute ELK Pipeline for a job.
    """
    meta = meta or {}
    correlation_id = meta.get("correlation_id") if isinstance(meta, dict) else None
    log_prefix = f"[{correlation_id}] " if correlation_id else ""
    logger.info(f"{log_prefix}Processing Job {job_id} [{pack_name}]")
    
    # Create DB Session
    # Note: Arq ctx["session_maker"] relies on startup context, 
    # but here we use our global get_session dependency pattern manually
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import AsyncSession
    
    async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. Update State -> PROCESSING
        db_job = await session.get(Job, job_id)
        if not db_job:
            logger.error(f"Job {job_id} not found in DB!")
            return
        
        db_job.status = JobStatus.PROCESSING
        db_job.updated_at = datetime.utcnow()
        await session.commit()
        
        try:
            # 2. Execute Pipeline
            # Load pipeline (cached by factory/registry)
            pipeline = load_pipeline(pack_name, {"whisper_model": "small"})
            
            # Run processing (CPU bound, but run in threadpool by app logic usually)
            # Here we are in a worker process, so blocking is 'okay' but threadpool is better
            # for heartbeat. However, WhisperX uses GPU/Torch which releases GIL often.
            
            # We call the synchronous pipeline directly.
            # Arq runs tasks in asyncio, so we wrap it
            import time
            start_time = time.perf_counter()
            
            result = await asyncio.to_thread(pipeline.process, audio_path)

            duration = time.perf_counter() - start_time
            
            # 3. Update State -> COMPLETED (or NEEDS_REVIEW)
            # Determine status based on confidence
            # (Assuming result has confidence metrics)
            final_status = JobStatus.COMPLETED
            
            # Simple heuristic: if confidence low, flag it
            # (You can implement logic here or inside pipeline)
            
            db_job.status = final_status
            db_job.result_data = result.model_dump() # EmergencyCall is Pydantic
            db_job.processing_time = duration
            db_job.updated_at = datetime.utcnow()
            
            await session.commit()
            logger.info(f"{log_prefix}Job {job_id} COMPLETED in {duration:.2f}s")

            # 4. Push to Connector (with timeout + retries)
            connector = ConnectorFactory.get_connector()
            payload = {
                "job_id": job_id,
                "pack": pack_name,
                "incident": db_job.result_data,
                "processing_time": duration,
                "correlation_id": correlation_id
            }

            for attempt in range(1, settings.CONNECTOR_MAX_RETRIES + 1):
                try:
                    await asyncio.wait_for(
                        connector.push_incident(payload),
                        timeout=settings.CONNECTOR_TIMEOUT
                    )
                    break
                except Exception as e:
                    logger.error(
                        f"{log_prefix}Connector push failed (attempt {attempt}/{settings.CONNECTOR_MAX_RETRIES}): {e}"
                    )
                    if attempt >= settings.CONNECTOR_MAX_RETRIES:
                        break
                    await asyncio.sleep(settings.CONNECTOR_RETRY_BASE_DELAY * (2 ** (attempt - 1)))
        except Exception as e:
            logger.error(f"{log_prefix}Job {job_id} FAILED: {e}")
            trace = traceback.format_exc()
            
            db_job.status = JobStatus.FAILED
            db_job.error_message = str(e)
            db_job.traceback = trace
            db_job.updated_at = datetime.utcnow()
            await session.commit()
            
            # Re-raise to let Arq handle retries? 
            # If we handle it here, it's "Done" but "Failed".
            # For this architecture, we mark FAILED in DB and don't retry indefinitely.

# Worker Settings
class WorkerSettings:
    functions = [process_audio_job]
    redis_settings = REDIS_SETTINGS
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = settings.MAX_CONCURRENT_JOBS
