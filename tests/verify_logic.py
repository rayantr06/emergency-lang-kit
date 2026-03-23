import asyncio
import os
import uuid
from unittest.mock import MagicMock, AsyncMock
from elk.api.routes import create_job
from elk.api.schemas import TranscribeRequest
from elk.core.config import settings
from elk.database.models import Job, JobStatus

async def test_create_job_logic():
    print("Testing create_job logic with asyncio.to_thread...")

    # Setup mocks
    mock_session = AsyncMock()
    mock_request_payload = TranscribeRequest(
        audio_base64="UklGRiAAAABXQVZFRm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=",
        language_hint="kab"
    )

    mock_fastapi_req = MagicMock()
    mock_fastapi_req.state.correlation_id = "test-corr-id"
    mock_fastapi_req.app.state.redis = AsyncMock()
    mock_fastapi_req.app.state.redis.llen.return_value = 0
    mock_fastapi_req.app.state.redis.enqueue_job.return_value = True

    mock_background_tasks = MagicMock()

    # Run create_job
    try:
        job = await create_job(
            request=mock_request_payload,
            fastapi_req=mock_fastapi_req,
            background_tasks=mock_background_tasks,
            session=mock_session
        )

        print(f"Job created successfully: {job.id}")
        assert job.status == JobStatus.QUEUED
        assert os.path.exists(job.input_data["file_path"])
        print(f"File saved at: {job.input_data['file_path']}")

        # Verify file content
        with open(job.input_data["file_path"], "rb") as f:
            content = f.read()
            assert len(content) > 0
            print("File content verified.")

        print("Test PASSED")

    except Exception as e:
        print(f"Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    # Ensure upload dir exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    asyncio.run(test_create_job_logic())
