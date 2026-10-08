import asyncio
import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from elk.database.models import Job, JobStatus


async def simulate_job(job_id, async_session, hold_connection=True):
    if hold_connection:
        async with async_session() as session:
            # Simulate DB get
            db_job = await session.get(Job, job_id)
            db_job.status = JobStatus.PROCESSING
            await session.commit()

            # Simulate pipeline.process
            await asyncio.sleep(1) # simulate 1s processing

            db_job = await session.get(Job, job_id)
            db_job.status = JobStatus.COMPLETED
            await session.commit()
    else:
        async with async_session() as session:
            db_job = await session.get(Job, job_id)
            db_job.status = JobStatus.PROCESSING
            await session.commit()

        await asyncio.sleep(1)

        async with async_session() as session:
            db_job = await session.get(Job, job_id)
            db_job.status = JobStatus.COMPLETED
            await session.commit()

async def main():
    # Use an engine with a small pool to show starvation
    engine = create_async_engine("sqlite+aiosqlite:///benchmark.db", pool_size=5, max_overflow=0)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create jobs
    job_ids = []
    async with async_session() as session:
        for _ in range(20):
            job_id = str(uuid.uuid4())
            job = Job(id=job_id, status=JobStatus.QUEUED, pack_name="test_pack", input_data={})
            session.add(job)
            job_ids.append(job_id)
        await session.commit()

    # Run with holding connection
    print("Testing with holding connection...")
    start = time.time()
    await asyncio.gather(*(simulate_job(jid, async_session, hold_connection=True) for jid in job_ids[:10]))
    print(f"Time with holding connection: {time.time() - start:.2f}s")

    # Run without holding connection
    print("Testing without holding connection...")
    start = time.time()
    await asyncio.gather(*(simulate_job(jid, async_session, hold_connection=False) for jid in job_ids[10:]))
    print(f"Time without holding connection: {time.time() - start:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
