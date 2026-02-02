import base64
import shutil
from fastapi.testclient import TestClient
import pytest

from elk.api import app as app_module
from elk.core.config import settings


class FakeRedis:
    def __init__(self, depth: int = 0):
        self.depth = depth

    async def llen(self, key: str):
        return self.depth

    async def enqueue_job(self, *args, **kwargs):
        return True

    async def ping(self):
        return True


@pytest.fixture(autouse=True)
def reset_settings(tmp_path):
    # Isolate uploads and security settings per test
    settings.API_KEY = "test-key"
    settings.UPLOAD_DIR = str(tmp_path / "uploads")
    settings.MAX_QUEUE_SIZE = 1
    yield
    shutil.rmtree(settings.UPLOAD_DIR, ignore_errors=True)


@pytest.fixture
def audio_payload():
    audio_bytes = b"RIFFAAAAWAVEdata"
    return base64.b64encode(audio_bytes).decode()


def _prepare_client(redis_depth: int) -> TestClient:
    app = app_module.app
    app.state.redis = FakeRedis(depth=redis_depth)
    # Avoid hitting real services during tests
    app.router.on_startup.clear()
    app.router.on_shutdown.clear()
    return TestClient(app)


def test_api_key_required(audio_payload):
    client = _prepare_client(redis_depth=0)
    response = client.post(
        "/jobs",
        json={"audio_base64": audio_payload, "language_hint": "kab"},
    )
    assert response.status_code == 401


def test_queue_backpressure_returns_429(audio_payload):
    client = _prepare_client(redis_depth=5)
    headers = {"X-API-Key": settings.API_KEY}
    response = client.post(
        "/jobs",
        json={"audio_base64": audio_payload, "language_hint": "kab"},
        headers=headers,
    )
    assert response.status_code == 429
