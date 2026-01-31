"""
ELK Kernel - Base Pipeline
Abstract Logic for Emergency Call Processing
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..schemas.interfaces import EmergencyCall

class BasePipeline(ABC):
    """
    Abstract Base Class for all Language Pack Pipelines.
    Enforces the standard ELK processing flow:
    1. Transcribe (ASR)
    2. Normalize (Text clean-up)
    3. Extract (LLM/Regex)
    4. Validate (Schema Check)
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def transcribe(self, audio_path: str) -> str:
        """Step 1: Convert Audio to Raw Text"""
        pass

    @abstractmethod
    def normalize(self, raw_text: str) -> str:
        """Step 2: Clean up text (handle code-switching, dialect)"""
        pass

    @abstractmethod
    def extract(self, normalized_text: str) -> Dict[str, Any]:
        """Step 3: Extract structured entities (Incident, Location, etc)"""
        pass

    def process(self, audio_path: str) -> EmergencyCall:
        """
        Main execution flow (Template Method Pattern).
        Orchestrates the pipeline steps.
        """
        # 1. ASR
        raw_text = self.transcribe(audio_path)
        
        # 2. Normalize
        norm_text = self.normalize(raw_text)
        
        # 3. Extract
        entities = self.extract(norm_text)
        
        # 4. Construct Object
        # Note: Validation logic usually happens here or inside the extract method
        # This is a simplified construction for the base class
        return EmergencyCall(
            audio_file=audio_path,
            transcription_raw=raw_text,
            transcription_normalized=norm_text,
            **entities
        )
