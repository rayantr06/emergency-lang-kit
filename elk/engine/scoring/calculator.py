"""
ELK Kernel - Confidence Calculator
Implements FR-04: Evaluation & Calculator Logic

Formula from MASTER_VISION.md:
    confidence = w1*asr_score + w2*entity_match_score + w3*rag_hit_score

Where:
    - asr_score: Audio quality / transcription confidence (0-1)
    - entity_match_score: Percentage of required entities found (0-1)
    - rag_hit_score: Knowledge base match quality (0-1)
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from ..schemas.interfaces import EmergencyCall, IncidentType, UrgencyLevel


@dataclass
class ConfidenceResult:
    """Detailed breakdown of confidence calculation."""
    overall: float
    asr_score: float
    entity_score: float
    rag_score: float
    triggers_human_review: bool
    reasoning: str


class ConfidenceCalculator:
    """
    Calculates overall confidence score for emergency call extraction.
    
    Implements weighted formula per MASTER_VISION.md:
    confidence = w1*asr + w2*entity + w3*rag
    
    Default weights tuned for emergency dispatch priority:
    - ASR: 40% (critical for accurate transcription)
    - Entity: 35% (critical for dispatch decision)
    - RAG: 25% (helpful for verification)
    """
    
    # Required entity fields for a complete extraction
    REQUIRED_FIELDS = ["incident_type", "urgency", "location"]
    OPTIONAL_FIELDS = ["victims_count", "description", "injuries"]
    
    # Confidence threshold for human review
    HUMAN_REVIEW_THRESHOLD = 0.70  # per MASTER_VISION.md
    
    def __init__(
        self,
        asr_weight: float = 0.40,
        entity_weight: float = 0.35,
        rag_weight: float = 0.25
    ):
        """
        Initialize calculator with configurable weights.
        
        Args:
            asr_weight: Weight for ASR confidence (default 0.40)
            entity_weight: Weight for entity coverage (default 0.35)
            rag_weight: Weight for RAG hit quality (default 0.25)
        """
        # Validate weights sum to 1.0
        total = asr_weight + entity_weight + rag_weight
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        
        self.w_asr = asr_weight
        self.w_entity = entity_weight
        self.w_rag = rag_weight
    
    def calculate_asr_confidence(
        self,
        transcription: str,
        word_confidences: Optional[List[float]] = None,
        audio_duration: Optional[float] = None
    ) -> float:
        """
        Calculate ASR quality score.
        
        Uses multiple signals:
        1. Word-level confidence (if available from WhisperX)
        2. Transcription length vs audio duration ratio
        3. Presence of common error patterns
        """
        score = 0.0
        factors = 0
        
        # Factor 1: Word-level confidence (if available)
        if word_confidences and len(word_confidences) > 0:
            avg_word_conf = sum(word_confidences) / len(word_confidences)
            score += avg_word_conf
            factors += 1
        
        # Factor 2: Transcription quality heuristics
        if transcription:
            # Penalize very short transcriptions
            word_count = len(transcription.split())
            if word_count < 3:
                length_score = 0.3
            elif word_count < 10:
                length_score = 0.6
            else:
                length_score = 0.9
            score += length_score
            factors += 1
            
            # Factor 3: Check for common ASR error patterns
            error_patterns = [
                "...",  # Trailing/incomplete
                "[inaudible]",
                "???",
                "musique",  # Music/noise hallucination
            ]
            error_count = sum(1 for p in error_patterns if p.lower() in transcription.lower())
            error_score = max(0.0, 1.0 - (error_count * 0.2))
            score += error_score
            factors += 1
        
        # Factor 4: Duration ratio check
        if audio_duration and transcription:
            # Expected: ~2-3 words per second of speech
            expected_words = audio_duration * 2.5
            actual_words = len(transcription.split())
            ratio = actual_words / max(expected_words, 1)
            # Good range: 0.5 - 1.5
            if 0.5 <= ratio <= 1.5:
                duration_score = 0.9
            elif 0.3 <= ratio <= 2.0:
                duration_score = 0.6
            else:
                duration_score = 0.3
            score += duration_score
            factors += 1
        
        if factors == 0:
            return 0.5  # Default neutral score
        
        return min(1.0, score / factors)
    
    def calculate_entity_coverage(
        self,
        extracted: Dict[str, Any]
    ) -> float:
        """
        Calculate entity extraction completeness.
        
        Scores based on:
        - Required fields present and valid
        - Optional fields that add context
        - Field value quality (not UNKNOWN)
        """
        score = 0.0
        
        # Required fields (weighted higher)
        required_found = 0
        for field in self.REQUIRED_FIELDS:
            if field in extracted and extracted[field] is not None:
                value = extracted[field]
                # Check it's not UNKNOWN
                if hasattr(value, 'value') and 'UNKNOWN' in str(value.value).upper():
                    required_found += 0.3  # Partial credit
                elif value == "UNKNOWN" or (isinstance(value, str) and not value.strip()):
                    required_found += 0.3
                else:
                    required_found += 1.0
        
        required_score = required_found / len(self.REQUIRED_FIELDS)
        score += required_score * 0.7  # 70% weight for required
        
        # Optional fields (bonus)
        optional_found = 0
        for field in self.OPTIONAL_FIELDS:
            if field in extracted and extracted[field] is not None:
                value = extracted[field]
                if value and str(value).strip() and str(value) != "0":
                    optional_found += 1
        
        if self.OPTIONAL_FIELDS:
            optional_score = optional_found / len(self.OPTIONAL_FIELDS)
            score += optional_score * 0.3  # 30% weight for optional
        
        return min(1.0, score)
    
    def calculate_rag_score(
        self,
        rag_context: str,
        extracted_location: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate RAG (Knowledge Base) hit quality.
        
        Higher score if:
        - Location matches known entities
        - More context retrieved
        - Context used in extraction
        """
        if not rag_context or rag_context == "NO_CONTEXT_FOUND":
            return 0.0
        
        score = 0.0
        
        # Count RAG hits
        hit_count = rag_context.count("DETECTED_")
        if hit_count >= 3:
            score = 1.0
        elif hit_count >= 2:
            score = 0.8
        elif hit_count >= 1:
            score = 0.6
        
        # Bonus if location was specifically matched
        if "DETECTED_LOCATION" in rag_context:
            score = min(1.0, score + 0.2)
        
        # Verify extraction used RAG context
        if extracted_location:
            location_details = str(extracted_location.get("details", "")).lower()
            # Check if any RAG entity appears in extraction
            for line in rag_context.split("\n"):
                if ":" in line:
                    entity = line.split(":")[1].split("(")[0].strip().lower()
                    if entity in location_details:
                        score = min(1.0, score + 0.2)
                        break
        
        return score
    
    def calculate(
        self,
        transcription: str,
        extracted: Dict[str, Any],
        rag_context: str = "NO_CONTEXT_FOUND",
        word_confidences: Optional[List[float]] = None,
        audio_duration: Optional[float] = None
    ) -> ConfidenceResult:
        """
        Calculate overall confidence with detailed breakdown.
        
        Args:
            transcription: Raw transcription text
            extracted: Extracted entities dict
            rag_context: RAG retrieval results
            word_confidences: Per-word ASR confidences (optional)
            audio_duration: Audio length in seconds (optional)
            
        Returns:
            ConfidenceResult with overall score and breakdown
        """
        # Calculate component scores
        asr_score = self.calculate_asr_confidence(
            transcription, word_confidences, audio_duration
        )
        
        entity_score = self.calculate_entity_coverage(extracted)
        
        rag_score = self.calculate_rag_score(
            rag_context,
            extracted.get("location") if isinstance(extracted.get("location"), dict) else None
        )
        
        # Weighted combination
        overall = (
            self.w_asr * asr_score +
            self.w_entity * entity_score +
            self.w_rag * rag_score
        )
        
        # Determine if human review needed
        triggers_review = overall < self.HUMAN_REVIEW_THRESHOLD
        
        # Generate reasoning
        reasoning_parts = []
        if asr_score < 0.5:
            reasoning_parts.append("Low ASR quality")
        if entity_score < 0.5:
            reasoning_parts.append("Missing required entities")
        if rag_score == 0:
            reasoning_parts.append("No location verified")
        
        if triggers_review:
            reasoning = f"HUMAN_REVIEW_REQUIRED: {', '.join(reasoning_parts) or 'Overall confidence below threshold'}"
        else:
            reasoning = "Confidence acceptable for automated dispatch"
        
        return ConfidenceResult(
            overall=round(overall, 3),
            asr_score=round(asr_score, 3),
            entity_score=round(entity_score, 3),
            rag_score=round(rag_score, 3),
            triggers_human_review=triggers_review,
            reasoning=reasoning
        )
