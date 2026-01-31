"""
ELK Pack - Runtime Pipeline
Dialect: Kabyle (Bejaia) / Arabizi / French
Implementation of BasePipeline for DZ-Civil Protection
"""

from typing import Dict, Any
from elk.kernel.pipeline.base_pipeline import BasePipeline
from elk.kernel.schemas.interfaces import IncidentType, UrgencyLevel
from ..data.lexicon import DAIRATE_BEJAIA, COMMUNES_FLAT, QUARTIERS_BEJAIA, VOCAB_MAP

from elk.kernel.ai.llm import LLMClient
from elk.kernel.schemas.interfaces import EmergencyCall, IncidentType, UrgencyLevel, Location

class KabylePipeline(BasePipeline):
    """
    Specific implementation for decoding Mixed Kabyle/French emergency calls.
    Handles: Arabizi numeric chat, Code-switching, and Bejaia Geodata.
    Feature: Real-time Lexical RAG (Retrieval Augmented Generation).
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.llm = LLMClient() # Injects Gemini AI

    def transcribe(self, audio_path: str) -> str:
        # Production: self.whisper.transcribe(audio_path)
        # For Demo: Return different mock texts based on input to prove logic
        if "fire" in audio_path:
            return "Afu di ttejra n Akfadou !" # Fire in Akfadou
        return "Kayen accident fi route nationale 9 pres de Tichy"

    def normalize(self, raw_text: str) -> str:
        text = raw_text.lower()
        # Arabizi Mapping
        arabizi = {"3": "ɛ", "7": "ḥ", "9": "q", "5": "x", "8": "ɣ"}
        for k, v in arabizi.items():
            text = text.replace(k, v)
        for k, v in VOCAB_MAP.items():
            text = text.replace(k, v)
        return text.strip()

    def retrieve_context(self, text: str) -> str:
        """
        LEXICAL RAG: Retrieves known entities from the Knowledge Base (Lexicon).
        This is deterministic (No hallucinations on location names).
        """
        matches = []
        # Spatial Search (Communes)
        for commune in COMMUNES_FLAT:
            if commune.lower() in text:
                matches.append(f"DETECTED_LOCATION: {commune} (Commune de Bejaia)")
        
        # Micro-Spatial Search (Quartiers)
        for quartier in QUARTIERS_BEJAIA:
            if quartier.lower() in text:
                matches.append(f"DETECTED_LANDMARK: {quartier} (Quartier connu)")

        if not matches:
            return "NO_CONTEXT_FOUND"
        return "\n".join(matches)

    def extract(self, normalized_text: str) -> Dict[str, Any]:
        """
        AI-Powered Extraction (Gemini 1.5 Flash)
        Uses RAG Context to guide the LLM.
        """
        # 1. Retrieve Knowledge
        context = self.retrieve_context(normalized_text)
        
        # 2. Construct System Prompt
        system_prompt = f"""
        You are an Emergency Dispatch AI for North Algeria (Kabylie).
        Extract strict JSON data from the transcript.
        
        KNOWLEDGE BASE (RAG CONTEXT):
        {context}
        
        RULES:
        - If context matches a location, use it EXACTLY in 'location.details'.
        - Infer 'urgency' based on incident type (Fire=High, Cat=Low).
        - Translate 'Kabyle/Arabizi' into standard incident types.
        """

        # 3. Generate (Real AI)
        try:
            # We call the LLM to get the structured dictionary directly
            data = self.llm.generate_structured(
                system_prompt=system_prompt,
                user_input=normalized_text,
                response_schema=EmergencyCall
            )
            # We strip fields that BasePipeline adds later to avoid collision
            if "audio_file" in data: del data["audio_file"]
            if "transcription_raw" in data: del data["transcription_raw"]
            return data
            
        except Exception as e:
            print(f"⚠️ AI Failure, falling back to rules: {e}")
            # Fallback Logic (Safety Net)
            return {
                "incident_type": IncidentType.UNKNOWN,
                "urgency": UrgencyLevel.UNKNOWN,
                "confidence": 0.1
            }
