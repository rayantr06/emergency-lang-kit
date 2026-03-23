
import time
import os
import sqlite3
import json
import gc
from elk.training.dataset import TrainingDatabase, TrainingSample

def get_memory_usage():
    # Fallback if psutil is not available
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB
    except ImportError:
        # On Linux, we can check /proc/self/status
        try:
            with open('/proc/self/status') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        return float(line.split()[1]) / 1024  # MB
        except:
            return 0

def benchmark_dataset_retrieval():
    db_path = "perf_test.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    db = TrainingDatabase(db_path)

    # Insert a large number of samples
    num_samples = 100000
    print(f"Inserting {num_samples} samples...")

    batch_size = 10000
    for i in range(0, num_samples, batch_size):
        samples = []
        for j in range(i, min(i + batch_size, num_samples)):
            samples.append((
                f"hash_{j}",
                f"path/to/audio_{j}.wav",
                f"raw_{j}",
                f"golden_{j}",
                json.dumps(["tag1", "tag2"]),
                0,
                0.8,
                "2023-01-01T00:00:00",
                "user"
            ))

        db.conn.executemany("""
            INSERT INTO samples
            (audio_hash, audio_path, transcription_raw, transcription_golden,
             dialect_tags, is_test_set, quality_score, created_at, validated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, samples)
        db.conn.commit()

    print("Benchmark retrieval (generator implementation)...")

    gc.collect()
    mem_before = get_memory_usage()
    start_time = time.perf_counter()

    # Generator implementation
    results_gen = db.get_training_set(min_quality=0.0)

    count = 0
    peak_mem = mem_before
    for sample in results_gen:
        count += 1
        if count % 10000 == 0:
            current_mem = get_memory_usage()
            if current_mem > peak_mem:
                peak_mem = current_mem

    end_time = time.perf_counter()
    mem_after = get_memory_usage()

    print(f"Retrieved {count} samples")
    print(f"Time taken: {end_time - start_time:.4f} seconds")
    print(f"Peak memory usage: {peak_mem:.2f} MB (Increase: {peak_mem - mem_before:.2f} MB)")
    print(f"Final memory usage: {mem_after:.2f} MB")

    db.close()
    if os.path.exists(db_path):
        os.remove(db_path)

if __name__ == "__main__":
    benchmark_dataset_retrieval()
