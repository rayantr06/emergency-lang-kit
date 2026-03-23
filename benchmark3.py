import asyncio
import time


class DummySession:
    async def __aenter__(self):
        await asyncio.sleep(0.01) # checkout connection
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await asyncio.sleep(0.01) # return connection

class Pool:
    def __init__(self, size=2):
        self.sem = asyncio.Semaphore(size)

    def session(self):
        return PooledSession(self)

class PooledSession:
    def __init__(self, pool):
        self.pool = pool

    async def __aenter__(self):
        await self.pool.sem.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.pool.sem.release()

async def simulate_job(hold_connection=True, pool=None):
    if hold_connection:
        async with pool.session() as session:
            await asyncio.sleep(0.01) # update to PROCESSING
            await asyncio.sleep(1) # simulate pipeline.process
            await asyncio.sleep(0.01) # update to COMPLETED
    else:
        async with pool.session() as session:
            await asyncio.sleep(0.01) # update to PROCESSING

        await asyncio.sleep(1) # simulate pipeline.process

        async with pool.session() as session:
            await asyncio.sleep(0.01) # update to COMPLETED

async def main():
    pool = Pool(size=5) # Imagine 5 max DB connections

    print("Testing with holding connection (10 jobs, 5 connections)...")
    start = time.time()
    await asyncio.gather(*(simulate_job(hold_connection=True, pool=pool) for _ in range(10)))
    print(f"Time with holding connection: {time.time() - start:.2f}s")

    print("Testing without holding connection (10 jobs, 5 connections)...")
    start = time.time()
    await asyncio.gather(*(simulate_job(hold_connection=False, pool=pool) for _ in range(10)))
    print(f"Time without holding connection: {time.time() - start:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
