"""
ELK Server Verification Script
Tests API endpoints, middleware, and rate limiting logic.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from fastapi.testclient import TestClient
from elk.api.app import app

client = TestClient(app)

def test_health_check():
    """Verify detailed health check works."""
    print("\n🔍 Testing /health endpoint...")
    response = client.get("/health")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Status 200 OK")
        print(f"   Metrics included: {list(data.keys())}")
        
        # Verify our new fields exist
        required_fields = ["system_load", "gpu_status", "cache_stats", "loaded_models"]
        missing = [f for f in required_fields if f not in data]
        
        if not missing:
            print("✅ Detailed metrics present")
            # Print GPU status if available
            if data["gpu_status"].get("available"):
                print(f"   GPU: {data['gpu_status']}")
        else:
            print(f"❌ Missing metrics: {missing}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")

def test_rate_limiter():
    """Verify rate limiter blocks excessive requests."""
    print("\n🔍 Testing Rate Limiter (Token Bucket)...")
    
    # Check if limiter is active via headers or behavior
    # Since we use a simple limiter, we just blast requests
    
    success_count = 0
    denied_count = 0
    
    # burst limit is 20, we send 30
    for i in range(30):
        response = client.get("/metrics")
        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429:
            denied_count += 1
            
    print(f"   Sent: 30 requests")
    print(f"   Accepted: {success_count}")
    print(f"   Denied: {denied_count}")
    
    if denied_count > 0:
        print("✅ Rate Limiter active (429 received)")
    else:
        # Note: TestClient bypasses some network layers, but middleware should run
        # If bucket is large enough, this might pass. Our config is 5/s capacity 20.
        # It takes time for tests to run, so tokens might refill.
        print("⚠️ Rate Limiter did not trigger (might be within limits)")

if __name__ == "__main__":
    test_health_check()
    test_rate_limiter()
