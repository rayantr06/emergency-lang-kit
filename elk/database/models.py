"""
ELK Database Models
Defines the schema for the Job Orchestration system.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlmodel import JSON, Column, Field, SQLModel


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    NEEDS_REVIEW = "needs_review"
    COMPLETED = "completed"
    FAILED = "failed"

class Job(SQLModel, table=True):
    """
    Represents an asynchronous processing job.
    Tracks state, inputs, results, and timing.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    status: JobStatus = Field(default=JobStatus.QUEUED, index=True)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Data Payload (JSON stored as dict)
    input_data: dict[str, Any] = Field(sa_column=Column(JSON))
    result_data: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))

    # Error Handling
    error_message: str | None = None
    traceback: str | None = None

    # Metrics
    processing_time: float | None = None
    pack_name: str = Field(index=True)
