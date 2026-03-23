import asyncio
import os
import time
import statistics

# Simulate the environment
UPLOAD_DIR = "/tmp/elk/benchmark_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
SAMPLE_AUDIO_SIZE_MB = 10
SAMPLE_AUDIO_DATA = b"0" * (SAMPLE_AUDIO_SIZE_MB * 1024 * 1024)

def sync_write(file_path, data):
    """The current blocking implementation."""
    with open(file_path, "wb") as f:
        f.write(data)

async def measure_lag_during_io(write_func_async, iterations=20):
    lags = []
    stop_monitoring = False

    async def monitor():
        while not stop_monitoring:
            start = time.perf_counter()
            await asyncio.sleep(0.001) # More frequent monitoring
            lags.append(max(0, time.perf_counter() - start - 0.001))

    monitor_task = asyncio.create_task(monitor())

    # Let monitor start
    await asyncio.sleep(0.05)

    start_time = time.perf_counter()
    # Run 20 writes sequentially to see cumulative blocking
    for i in range(iterations):
        file_path = os.path.join(UPLOAD_DIR, f"file_{i}.wav")
        await write_func_async(file_path, SAMPLE_AUDIO_DATA)

    duration = time.perf_counter() - start_time
    stop_monitoring = True
    await monitor_task

    return duration, lags

async def main():
    print(f"--- ELK I/O Blocking Benchmark ---")
    print(f"File size: {SAMPLE_AUDIO_SIZE_MB}MB")

    # 1. Baseline (Sync/Blocking)
    print("\n[Phase 1: Baseline - Blocking I/O]")

    async def blocking_wrapper(path, data):
        sync_write(path, data)

    sync_dur, sync_lags = await measure_lag_during_io(blocking_wrapper)
    print(f"Total time (20 iterations): {sync_dur:.4f}s")
    if sync_lags:
        print(f"Max event loop lag: {max(sync_lags)*1000:.2f}ms")
        print(f"Avg event loop lag: {statistics.mean(sync_lags)*1000:.2f}ms")
        print(f"Total samples > 10ms: {sum(1 for l in sync_lags if l > 0.01)}")
    else:
        print("No lag data collected.")

    # 2. Optimized (asyncio.to_thread)
    print("\n[Phase 2: Optimized - Non-blocking I/O]")

    async def optimized_wrapper(path, data):
        await asyncio.to_thread(sync_write, path, data)

    opt_dur, opt_lags = await measure_lag_during_io(optimized_wrapper)
    print(f"Total time (20 iterations): {opt_dur:.4f}s")
    if opt_lags:
        print(f"Max event loop lag: {max(opt_lags)*1000:.2f}ms")
        print(f"Avg event loop lag: {statistics.mean(opt_lags)*1000:.2f}ms")
        print(f"Total samples > 10ms: {sum(1 for l in opt_lags if l > 0.01)}")
    else:
        print("No lag data collected.")

    print("\n--- Summary ---")
    if sync_lags and opt_lags:
        improvement = (max(sync_lags) - max(opt_lags)) / max(sync_lags) * 100
        print(f"Max lag reduction: {improvement:.2f}%")

        avg_improvement = (statistics.mean(sync_lags) - statistics.mean(opt_lags)) / statistics.mean(sync_lags) * 100
        print(f"Avg lag reduction: {avg_improvement:.2f}%")

if __name__ == "__main__":
    asyncio.run(main())
