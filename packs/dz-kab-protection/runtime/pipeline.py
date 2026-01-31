"""
ELK Pack - Runtime Pipeline
Dialect: Kabyle (Bejaia) / Arabizi / French
Implementation of BasePipeline for DZ-Civil Protection
"""

from typing import Dict, Any
from elk.kernel.pipeline.base_pipeline import BasePipeline
from elk.kernel.schemas.interfaces import IncidentType, UrgencyLevel
from ..data.lexicon import DAIRATE_BEJAIA, COMMUNES_FLAT, QUARTIERS_BEJAIA, VOCAB_MAP

class KabylePipeline(BasePipeline):
    """
    Specific implementation for decoding Mixed Kabyle/French emergency calls.
    Handles: Arabizi numeric chat, Code-switching, and Bejaia Geodata.
    """

    def transcribe(self, audio_path: str) -> str:
        """
        Uses WhisperX or Optimized Whisper model.
        For migration demo, we simulate or wrap the legacy call.
        """
        # In production, this would call self.whisper_model.transcribe()
        return f"[MOCK TRANSCRIPT of {audio_path}]"

    def normalize(self, raw_text: str) -> str:
        """
        Specialized Arabizi Normalization
        3 -> ɛ, 7 -> ḥ, etc.
        """
        text = raw_text.lower()
        
        # 1. Arabizi Mapping
        arabizi = {"3": "ɛ", "7": "ḥ", "9": "q", "5": "x", "8": "ɣ"}
        for k, v in arabizi.items():
            text = text.replace(k, v)
            
        # 2. Vocab Mapping (from Lexicon)
        for k, v in VOCAB_MAP.items():
            text = text.replace(k, v)
            
        return text.strip()

    def extract(self, normalized_text: str) -> Dict[str, Any]:
        """
        Rule-based extraction using Bejaia Lexicon.
        (In V2, this delegates to Gemini 1.5 Flash)
        """
        data = {}
        
        # 1. Location Search
        for commune in COMMUNES_FLAT:
            if commune.lower() in normalized_text:
                data["location"] = {"raw_text": commune, "details": {"commune": commune}}
                break
        
        # 2. Incident Search (Simplified)
        if "incendie" in normalized_text or "feu" in normalized_text:
            data["incident_type"] = IncidentType.FIRE_BUILDING
            data["urgency"] = UrgencyLevel.HIGH
        elif "accident" in normalized_text:
            data["incident_type"] = IncidentType.ACCIDENT_VEHICULAR
            data["urgency"] = UrgencyLevel.MEDIUM
            
        # 3. Default
        if "incident_type" not in data:
            data["incident_type"] = IncidentType.UNKNOWN
            data["urgency"] = UrgencyLevel.UNKNOWN
            
        return data
