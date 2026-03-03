# Performance Rationale: Offloading Blocking I/O in Async Middleware

## The Problem
The `StructuredLogger` in `elk/api/middleware.py` performs synchronous file I/O operations (`open()` and `write()`) directly within the asynchronous `dispatch` method of the `RequestLoggingMiddleware`.

In an asynchronous application (FastAPI/Starlette), all requests are typically handled by a single event loop. When a blocking call like synchronous file I/O is made:
1. The entire event loop is paused.
2. No other concurrent requests can be processed during this time.
3. Total system throughput decreases and latency increases, especially under high load.

## The Solution: `asyncio.to_thread`
By using `asyncio.to_thread` (available in Python 3.9+), we can offload these blocking I/O operations to a separate thread from the internal thread pool.
- This allows the event loop to continue processing other requests while the file I/O happens in the background.
- It prevents "event loop starvation".

## Theoretical Improvement
- **Concurrency**: High. Other requests are not blocked by logging.
- **Latency**: Reduced for concurrent requests.
- **Throughput**: Increased, as the CPU can spend more time handling logic and less time waiting for disk I/O in the main thread.

## Serialization Optimization
In addition to I/O offloading, using `orjson` (when available) for JSON serialization provides a significant speedup (3-10x) over the standard `json` library, reducing CPU time spent in the middleware.
