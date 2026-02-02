"""
ELK Database Models
Defines the schema for the Job Orchestration system.
"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON
import uuid

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
    input_data: Dict[str, Any] = Field(sa_column=Column(JSON))
    result_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Error Handling
    error_message: Optional[str] = None
    traceback: Optional[str] = None
    
    # Metrics
    processing_time: Optional[float] = None
    pack_name: str = Field(index=True)
