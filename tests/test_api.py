from elk.server.schemas import TranscribeRequest

def test_health_check(client):
    """Test GET /health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "dz-kab-protection" in data["active_packs"]

def test_process_endpoint_mock(client):
    """Test POST /v1/process with mock data"""
    payload = {
        "audio_base64": "SGVsbG8gV29ybGQ=", # "Hello World" in base64
        "language_hint": "kab"
    }
    response = client.post("/v1/process", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure matches ProcessResponse schema
    assert "call_id" in data
    assert data["status"] == "success"
    assert data["result"]["incident_type"] == "fire_forest" # Matches MockPipeline output
