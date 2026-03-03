
import asyncio
import time
import json
import os
import shutil
from pathlib import Path
from elk.api.middleware import StructuredLogger

async def benchmark_logger():
    log_dir = "test_logs"
    if os.path.exists(log_dir):
        shutil.rmtree(log_dir)

    logger = StructuredLogger(log_dir=log_dir)
    data = {"test": "data", "value": 123}

    iterations = 100

    print(f"Running baseline benchmark with {iterations} iterations...")

    start_time = time.perf_counter()
    for _ in range(iterations):
        # Now async, so we must await it
        await logger.log_request(data)
    end_time = time.perf_counter()

    total_time = end_time - start_time
    print(f"Total time for {iterations} asynchronous logs: {total_time:.4f}s")
    print(f"Average time per log: {(total_time/iterations)*1000:.4f}ms")

    # Now simulate concurrent requests and see how offloading affects them
    print("\nSimulating concurrent requests with offloaded I/O...")

    async def task(id):
        start = time.perf_counter()
        # Simulate some async work
        await asyncio.sleep(0.01)
        # Call offloaded logger (async)
        await logger.log_request({"task_id": id})
        return time.perf_counter() - start

    start_time = time.perf_counter()
    tasks = [task(i) for i in range(iterations)]
    latencies = await asyncio.gather(*tasks)
    end_time = time.perf_counter()

    total_time = end_time - start_time
    avg_latency = sum(latencies) / len(latencies)

    print(f"Total time for {iterations} concurrent tasks: {total_time:.4f}s")
    print(f"Average latency per task: {avg_latency*1000:.4f}ms")

    if os.path.exists(log_dir):
        shutil.rmtree(log_dir)

if __name__ == "__main__":
    asyncio.run(benchmark_logger())
