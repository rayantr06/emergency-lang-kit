from elk.api.schemas import TranscribeRequest
from elk.core.config import settings

def _get_headers():
    headers = {}
    if settings.API_KEY:
        headers["X-API-Key"] = settings.API_KEY
    return headers

def test_health_check(client):
    """Test GET /health endpoint (Auth bypass usually allowed for health)"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_create_job_endpoint(client):
    """Test POST /jobs endpoint for async job creation"""
    payload = {
        "audio_base64": "UklGRiAAAABXQVZFRm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=", # Dummy WAV header
        "language_hint": "kab"
    }
    response = client.post("/jobs", json=payload, headers=_get_headers())
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "queued"

def test_get_job_status_not_found(client):
    """Test GET /jobs/{id} for non-existent job"""
    response = client.get("/jobs/not-found-id", headers=_get_headers())
    assert response.status_code == 404
