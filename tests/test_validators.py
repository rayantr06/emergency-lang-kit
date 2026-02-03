import pytest
from pydantic import ValidationError
from elk.engine.schemas.interfaces import EmergencyCall, IncidentType, UrgencyLevel, Location

def test_valid_emergency_call():
    """Test creating a valid EmergencyCall object"""
    call = EmergencyCall(
        audio_file="test.wav",
        transcription_raw="Feu a la foret de Akfadou",
        incident_type=IncidentType.FIRE_FOREST,
        urgency=UrgencyLevel.CRITICAL,
        confidence=0.95
    )
    assert call.incident_type == IncidentType.FIRE_FOREST
    assert call.urgency == UrgencyLevel.CRITICAL

def test_invalid_urgency_raises_error():
    """Test that invalid urgency strings raise ValidationError"""
    with pytest.raises(ValidationError):
        EmergencyCall(
            audio_file="test.wav",
            transcription_raw="Test",
            incident_type=IncidentType.OTHER,
            urgency="SUPER_URGENT", # Invalid enum value
            confidence=0.5
        )

def test_location_structure():
    """Test nested Location object"""
    loc = Location(
        raw_text="Akfadou",
        details={"wilaya": "Bejaia"}
    )
    assert loc.details["wilaya"] == "Bejaia"
    assert loc.details.get("commune") is None # Optional field
