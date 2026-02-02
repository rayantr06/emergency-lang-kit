import pytest
from fastapi.testclient import TestClient
from elk.api.app import app
from elk.database.db import engine
from sqlmodel import SQLModel

class MockRedis:
    async def llen(self, key): return 0
    async def enqueue_job(self, *args, **kwargs): return True
    async def ping(self): return True
    async def close(self): pass

@pytest.fixture(autouse=True)
def init_test_db():
    """Initialize test database tables."""
    SQLModel.metadata.create_all(engine)
    yield
    # We could drop all here if needed for isolation

@pytest.fixture
def client():
    """
    Fixture for FastAPI TestClient with Mocked Redis.
    """
    app.state.redis = MockRedis()
    # Disable startup/shutdown to avoid real DB/Redis init during client creation
    app.router.on_startup.clear()
    app.router.on_shutdown.clear()
    return TestClient(app)
