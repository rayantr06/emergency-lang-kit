"""
ELK API Routes
Handles Job creation and status retrieval.
"""

import os
import base64
import uuid
import asyncio
import time
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from elk.database.db import get_session
from elk.database.models import Job, JobStatus
from elk.api.schemas import TranscribeRequest
from elk.core.config import settings
from elk.engine.schemas.interfaces import EmergencyCall

router = APIRouter()

@router.post("/jobs", response_model=Job, status_code=201)
async def create_job(
    request: TranscribeRequest,
    fastapi_req: Request, # Access app.state
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session)
):
    """
    Submit a new job for asynchronous processing.
    """
    job_id = str(uuid.uuid4())
    correlation_id = getattr(fastapi_req.state, "correlation_id", str(uuid.uuid4())[:8])

    # 1. Safety Check: Verify Audio Size
    try:
        audio_data = base64.b64decode(request.audio_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 audio payload")
    size_mb = len(audio_data) / (1024 * 1024)
    if size_mb > settings.MAX_AUDIO_SIZE_MB:
        raise HTTPException(
            status_code=413, 
            detail=f"Audio too large ({size_mb:.1f}MB). Max: {settings.MAX_AUDIO_SIZE_MB}MB"
        )

    if not _is_supported_audio(audio_data):
        raise HTTPException(status_code=415, detail="Unsupported audio format")

    # 1b. Queue Backpressure
    redis = getattr(fastapi_req.app.state, "redis", None)
    if not redis:
        raise HTTPException(status_code=503, detail="Queue unavailable")
    try:
        queue_depth = await asyncio.wait_for(redis.llen("arq:queue"), timeout=settings.QUEUE_OP_TIMEOUT)
    except Exception:
        raise HTTPException(status_code=503, detail="Queue check failed")
    if queue_depth >= settings.MAX_QUEUE_SIZE:
        raise HTTPException(status_code=429, detail="Queue is full, retry later")

    # 2. Save Audio File
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, f"{job_id}.wav")

    # Run cleanup in background to keep ingestion latency low
    background_tasks.add_task(_cleanup_old_uploads)

    try:
        with open(file_path, "wb") as f:
            f.write(audio_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {e}")

    # 3. Create Job Record
    job = Job(
        id=job_id,
        status=JobStatus.QUEUED,
        pack_name="dz-kab-protection",
        input_data={"file_path": file_path, "hint": request.language_hint, "correlation_id": correlation_id}
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    
    # 4. Enqueue Task (Using cached Redis pool)
    try:
        await asyncio.wait_for(
            fastapi_req.app.state.redis.enqueue_job(
                'process_audio_job',
                job_id=job_id,
                pack_name=job.pack_name,
                audio_path=file_path,
                meta={"orig_lang": request.language_hint, "correlation_id": correlation_id}
            ),
            timeout=settings.QUEUE_OP_TIMEOUT
        )
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error_message = f"Enqueue failed: {e}"
        await session.commit()
        raise HTTPException(status_code=500, detail="Failed to enqueue job")
        
    return job

@router.get("/jobs/{job_id}", response_model=Job)
async def get_job(
    job_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get Job Status and Result."""
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/jobs", response_model=List[Job])
async def list_jobs(
    limit: int = 10,
    offset: int = 0,
    session: AsyncSession = Depends(get_session)
):
    """List recent jobs."""
    # statement = select(Job).order_by(Job.created_at.desc()).offset(offset).limit(limit)
    # result = await session.exec(statement)
    # return result.all()
    # SQLModel exec with async session needs work, standard SQLAlchemy select:
    result = await session.execute(
        select(Job).order_by(Job.created_at.desc()).offset(offset).limit(limit)
    )
    return result.scalars().all()


def _is_supported_audio(data: bytes) -> bool:
    """Very small header check for WAV/ID3/MP3 frames."""
    if len(data) < 4:
        return False
    if data.startswith(b"RIFF") and b"WAVE" in data[:16]:
        return True
    if data.startswith(b"ID3"):
        return True
    if data[0:2] == b"\xff\xfb" or data[0:2] == b"\xff\xf3":
        return True
    return False


def _cleanup_old_uploads():
    """Remove old uploaded files based on TTL to protect disk usage."""
    cutoff = time.time() - settings.UPLOAD_TTL_SECONDS
    if not os.path.isdir(settings.UPLOAD_DIR):
        return
    for entry in os.scandir(settings.UPLOAD_DIR):
        try:
            if entry.is_file() and entry.stat().st_mtime < cutoff:
                os.remove(entry.path)
        except Exception:
            continue
