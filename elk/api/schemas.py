from typing import Any

from pydantic import BaseModel, Field

from elk.engine.schemas.interfaces import EmergencyCall


# Request Models
class TranscribeRequest(BaseModel):
    audio_base64: str = Field(..., description="Base64 encoded audio content")
    language_hint: str | None = Field("kab", description="Language code hint (kab, ara, fra)")

class ExtractRequest(BaseModel):
    transcript: str = Field(..., description="Text to analyze")
    context: dict[str, Any] | None = Field(default_factory=dict, description="Additional context (e.g., location metadata)")

# Response Models
class ProcessResponse(BaseModel):
    """Unified Response for End-to-End Processing"""
    call_id: str
    status: str
    result: EmergencyCall
    processing_time: float

class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0"
    active_packs: list[str]
    system_load: dict[str, float] | None = None
    gpu_status: dict[str, Any] | None = None
    cache_stats: dict[str, Any] | None = None
    loaded_models: dict[str, Any] | None = None
    dependencies: dict[str, str] | None = None
