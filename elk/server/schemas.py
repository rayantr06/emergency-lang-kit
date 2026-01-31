from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from elk.kernel.schemas.interfaces import EmergencyCall, IncidentType, UrgencyLevel

# Request Models
class TranscribeRequest(BaseModel):
    audio_base64: str = Field(..., description="Base64 encoded audio content")
    language_hint: Optional[str] = Field("kab", description="Language code hint (kab, ara, fra)")

class ExtractRequest(BaseModel):
    transcript: str = Field(..., description="Text to analyze")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context (e.g., location metadata)")

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
