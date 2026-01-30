from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from enum import Enum
from datetime import datetime
import uuid

# --- 1. DOMAIN ENUMS (The Controlled Vocabulary) ---
class UrgencyLevel(str, Enum):
    """
    Standardized Urgency Levels for triage.
    """
    LOW = "low"         # e.g., Cat stuck in tree
    MEDIUM = "medium"   # e.g., Minor traffic accident, no injuries
    HIGH = "high"       # e.g., Fire, Assault, Injuries
    CRITICAL = "critical" # e.g., Cardiac Arrest, Mass Casualty, Terrorism
    UNKNOWN = "unknown"

class IncidentType(str, Enum):
    """
    Top-level classification events.
    Each Language Pack maps local keywords to these keys.
    """
    FIRE = "fire"
    MEDICAL = "medical"
    POLICE = "police"
    CIVIL_DISORDER = "civil_disorder"
    TRAFFIC = "traffic"
    OTHER = "other"

# --- 2. ENTITY MODEL (The 'What/Where/Who') ---
class LocationEntity(BaseModel):
    raw_text: str = Field(..., description="The original mention in the text")
    normalized_address: Optional[str] = Field(None, description="Google Maps / GIS valid address")
    place_type: Literal["residence", "public_space", "highway", "unknown"]
    coordinates: Optional[List[float]] = Field(None, description="[Lat, Lon]")

class Entities(BaseModel):
    location: Optional[LocationEntity] = None
    casualties: Optional[int] = Field(None, description="Estimated number of victims")
    hazards: List[str] = Field(default_factory=list, description="e.g. ['gas', 'smoke', 'weapon']")

# --- 3. THE KERNEL STATE (The Single Source of Truth) ---
class OperationalState(BaseModel):
    """
    Represents the full context of an emergency call at a specific timestamp.
    This object is what evolves through the Kinetic Pipeline.
    """
    call_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Ingestion Layer
    transcription: str
    language_detected: str = Field(..., description="ISO code e.g. 'fr-FR', 'kab-DZ'")
    
    # Semantic Layer (The Understanding)
    incident_type: IncidentType
    urgency: UrgencyLevel
    
    # Entity Layer (The Details)
    entities: Entities
    
    # Meta-Cognition (Safety Layer)
    confidence_score: float = Field(..., ge=0, le=1, description="Global confidence of the AI")
    reasoning_trace: str = Field(..., description="Structured explanation of WHY this decision was made")

    class Config:
        use_enum_values = True
        extra = "forbid"  # Strict Schema: Disallow unknown fields (Hallucination prevention)

# --- 4. DECISION INTERFACE (Output to Dispatch) ---
class DecisionProposal(BaseModel):
    action: Literal["dispatch", "escalate_to_human", "ask_info"]
    target_unit: Optional[str] = Field(None, description="e.g. 'Station 4', 'Police HQ'")
    priority: int = Field(..., ge=1, le=5)
    rationale: str
