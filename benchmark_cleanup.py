import asyncio
import os
import time
import tempfile
from elk.core.config import settings
from elk.api.routes import _cleanup_old_uploads

async def run_benchmark():
    # Setup dummy directory
    old_dir = settings.UPLOAD_DIR
    temp_dir = tempfile.mkdtemp()
    settings.UPLOAD_DIR = temp_dir

    num_files = 50000
    print(f"Creating {num_files} dummy files in {temp_dir}...")

    # Batch create files
    now = time.time()
    old_time = now - 100000
    for i in range(num_files):
        file_path = os.path.join(temp_dir, f"dummy_{i}.wav")
        # Create empty file
        open(file_path, 'a').close()
        os.utime(file_path, (old_time, old_time))

    print("Measuring event loop block duration...")

    # Task that checks event loop responsiveness
    async def monitor_loop():
        delays = []
        start = time.perf_counter()
        while time.perf_counter() - start < 3: # Monitor for up to 3 seconds
            t0 = time.perf_counter()
            await asyncio.sleep(0.01)
            t1 = time.perf_counter()
            delays.append(t1 - t0 - 0.01)
        return max(delays) if delays else 0

    monitor_task = asyncio.create_task(monitor_loop())

    # Wait a tiny bit for the monitor to start
    await asyncio.sleep(0.05)

    # Run the cleanup task, which is what we are testing
    t0 = time.perf_counter()
    if asyncio.iscoroutinefunction(_cleanup_old_uploads):
        await _cleanup_old_uploads()
    else:
        _cleanup_old_uploads()
    duration = time.perf_counter() - t0

    # Wait for monitor to finish
    max_delay = await monitor_task

    print(f"Cleanup took: {duration:.4f} seconds")
    print(f"Max event loop blocked for: {max_delay:.4f} seconds")

    # Check if files were deleted
    remaining = len(os.listdir(temp_dir))
    print(f"Remaining files: {remaining}")

    # Cleanup
    settings.UPLOAD_DIR = old_dir
    try:
        os.rmdir(temp_dir)
    except Exception as e:
        print(f"Failed to remove temp dir: {e}")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
