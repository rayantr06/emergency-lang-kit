#!/usr/bin/env python3
"""
ELK Enterprise Benchmarking Tool
Measures end-to-end latency: API Request -> Queue -> Worker -> DB Result.
"""

import asyncio
import time
import httpx
import uuid
import sys
import statistics
from typing import List

# Configuration
API_URL = "http://localhost:8000"
CONCURRENT_REQUESTS = 5
SAMPLE_FILE = "demo.wav" # Ensure this exists in root for testing

async def submit_and_wait(client: httpx.AsyncClient, job_name: str):
    """Submits a job and polls for completion."""
    start = time.perf_counter()
    
    # 1. Submit Job
    try:
        # Note: In real benchmark, we'd use a real file.
        # Here we simulate the multipart upload.
        files = {'file': (SAMPLE_FILE, open(SAMPLE_FILE, 'rb'), 'audio/wav')}
        response = await client.post(f"{API_URL}/jobs", files=files)
        response.raise_for_status()
        job = response.json()
        job_id = job['id']
    except Exception as e:
        print(f"Error submitting {job_name}: {e}")
        return None

    # 2. Poll for Completion
    wait_start = time.perf_counter()
    while True:
        await asyncio.sleep(1.0) # Check every second
        resp = await client.get(f"{API_URL}/jobs/{job_id}")
        data = resp.json()
        
        status = data['status']
        if status in ['completed', 'failed']:
            end = time.perf_counter()
            total_time = end - start
            process_time = data.get('processing_time', 0)
            queue_time = total_time - process_time
            
            return {
                "id": job_id,
                "status": status,
                "total_latency": total_latency,
                "processing_latency": process_time,
                "queue_latency": queue_time
            }
        
        if (time.perf_counter() - wait_start) > 60: # 60s timeout
            return {"id": job_id, "status": "timeout", "total_latency": 60}

async def run_benchmark():
    print(f"Starting ELK Benchmark: {CONCURRENT_REQUESTS} concurrent requests")
    print(f"Target: {API_URL}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [submit_and_wait(client, f"Job-{i}") for i in range(CONCURRENT_REQUESTS)]
        results = await asyncio.gather(*tasks)
        
    # Process Stats
    valid_results = [r for r in results if r and r['status'] == 'completed']
    if not valid_results:
        print("No successful jobs completed. Ensure API and Worker are running.")
        return

    latencies = [r['total_latency'] for r in valid_results]
    p_times = [r['processing_latency'] for r in valid_results]
    
    print("\n--- PERFORMANCE REPORT ---")
    print(f"Success Rate: {len(valid_results)}/{CONCURRENT_REQUESTS}")
    print(f"Average End-to-End Latency: {statistics.mean(latencies):.2f}s")
    print(f"P50 Latency: {statistics.median(latencies):.2f}s")
    if len(latencies) > 1:
        print(f"P95 Latency: {statistics.quantiles(latencies, n=20)[18]:.2f}s") # Approximating P95
    print(f"Avg Worker Processing Time: {statistics.mean(p_times):.2f}s")
    print("--------------------------\n")

if __name__ == "__main__":
    # Create dummy wav if it doesn't exist just for the benchmark script to not crash
    import os
    if not os.path.exists(SAMPLE_FILE):
        with open(SAMPLE_FILE, "wb") as f:
            f.write(b"RIFF\x00\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00@\x1f\x00\x00@\x1f\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00")
            
    asyncio.run(run_benchmark())
