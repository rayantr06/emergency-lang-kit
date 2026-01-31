import pytest
from fastapi.testclient import TestClient
from elk.server.app import app

@pytest.fixture
def client():
    """
    Fixture for FastAPI TestClient.
    Allows simulating API requests without running the server.
    """
    return TestClient(app)
