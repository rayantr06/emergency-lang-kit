"""
ELK Kernel - Standard Interfaces
Universal Emergency Ontology
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# 1. Standard Enums (Universal)
class IncidentType(str, Enum):
    UNKNOWN = "unknown"
    ACCIDENT_VEHICULAR = "accident_vehicular"
    ACCIDENT_PEDESTRIAN = "accident_pedestrian"
    FIRE_BUILDING = "fire_building"
    FIRE_FOREST = "fire_forest"
    FIRE_VEHICLE = "fire_vehicle"
    MEDICAL_EMERGENCY = "medical_emergency"
    DROWNING = "drowning"
    ASSAULT_VIOLENCE = "assault_violence"
    THEFT_ROBBERY = "theft_robbery"
    NATURAL_DISASTER = "natural_disaster"
    HAZMAT = "hazmat"
    LOST_PERSON = "lost_person"
    STRUCTURAL_COLLAPSE = "structural_collapse"
    OTHER = "other"

class UrgencyLevel(str, Enum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TriState(str, Enum):
    UNKNOWN = "unknown"
    NO = "no"
    YES = "yes"

class Intent(str, Enum):
    REPORT_INCIDENT = "report_incident"
    REQUEST_HELP = "request_help"
    UPDATE_INFO = "update_info"
    FALSE_ALARM = "false_alarm"
    OTHER = "other"

# 2. Ontology Objects
class Location(BaseModel):
    """Universal Location Object"""
    raw_text: str = Field(..., description="Raw text mentioning location")
    # Region specific fields will be handled via dynamic dict or subclassing in Packs
    details: dict[str, Any] = Field(default_factory=dict, description="Structured address components (city, street, etc)")
    coordinates: str | None = Field(None, description="GPS Coordinates")

class EmergencyCall(BaseModel):
    """Central Entity - Universal Structure"""
    audio_file: str
    call_id: str | None = None

    # Transcription
    transcription_raw: str
    transcription_normalized: str | None = None

    # Extraction
    incident_type: IncidentType = Field(IncidentType.UNKNOWN)
    location: Location | None = None
    victims_count: int | None = None
    urgency: UrgencyLevel = Field(UrgencyLevel.UNKNOWN)

    # Metadata
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    language_detected: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

    # Human Loop
    needs_review: bool = False
    review_reason: str | None = None

    model_config = ConfigDict(use_enum_values=True)
