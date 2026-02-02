import requests
import base64
import json
import time
import sys

# Configuration
API_URL = "http://localhost:8000"
API_KEY = "elk-dev-key-2026" # Ensure this matches your .env or settings

def run_demo():
    print("🚀 ELK API Demo: Submitting Emergency Job...")
    
    # 1. Prepare Dummy Audio (WAV Header)
    audio_content = b"RIFF" + b"\x00" * 36 + b"WAVEfmt " + b"\x10" * 4 + b"data" + b"\x00" * 4
    audio_base64 = base64.b64encode(audio_content).decode('utf-8')
    
    payload = {
        "audio_base64": audio_base64,
        "language_hint": "dz-kab"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    # 2. POST /jobs
    try:
        print(f"📡 Sending request to {API_URL}/jobs...")
        response = requests.post(f"{API_URL}/jobs", json=payload, headers=headers)
        
        if response.status_code == 401:
            print("❌ Unauthorized: Please check your API_KEY configuration.")
            return

        response.raise_for_status()
        job = response.json()
        job_id = job['id']
        print(f"✅ Job Created! ID: {job_id} | Status: {job['status']}")
        
        # 3. Poll for status
        print("⏳ Polling for job completion (Simulating worker delay)...")
        for _ in range(5):
            time.sleep(2)
            res = requests.get(f"{API_URL}/jobs/{job_id}", headers=headers)
            res.raise_for_status()
            status_data = res.json()
            print(f"   Current Status: {status_data['status']}")
            if status_data['status'] in ['completed', 'failed']:
                break
                
        print("\n🏁 Demo Finished.")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: ELK API is not running. Did you run 'docker-compose up'?")
    except Exception as e:
        print(f"❌ Error during demo: {e}")

if __name__ == "__main__":
    run_demo()
