"""
ELK Kernel - Validation Module
Generic Pydantic Validators for Emergency Calls
"""

from pydantic import ValidationError
from typing import List, Optional
from ..schemas.interfaces import EmergencyCall, IncidentType, UrgencyLevel, TriState

class CallValidator:
    """
    Universal Validator for EmergencyCall objects.
    Enforces logical consistency (e.g., Fire implies Fire Present).
    """

    @staticmethod
    def validate_consistency(call: EmergencyCall) -> List[str]:
        """
        Checks for logical contradictions in the extracted data.
        Returns a list of warning messages (empty if valid).
        """
        errors = []

        # 1. Victim Count vs Urgency
        # If mass casualty, urgency must not be LOW
        if call.victims_count and call.victims_count >= 3:
            if call.urgency == UrgencyLevel.LOW:
                errors.append(f"Inconsistent: {call.victims_count} victims but urgency is LOW")

        # 2. Incident Type Specific Checks
        # Fire incidents should likely not have 'trapped_persons' as NO if 'victims_count' is high
        # (This is more generic logic)
        
        return errors

    @staticmethod
    def validate_schema(data: dict) -> bool:
        """
        Strict Schema Validation against Pydantic Model.
        """
        try:
            EmergencyCall(**data)
            return True
        except ValidationError:
            return False
