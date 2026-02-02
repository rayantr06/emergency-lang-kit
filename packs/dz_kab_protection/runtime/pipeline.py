"""
ELK Pack - Runtime Pipeline
Dialect: Kabyle (Bejaia) / Arabizi / French
Implementation of BasePipeline for DZ-Civil Protection

Uses WhisperX for optimized ASR with:
- Faster inference than Faster-Whisper
- Word-level alignment (wav2vec2)
- Batch processing
- Optimized Béjaïa-style French prompt
"""

import os
import re
import logging
from typing import Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

# Optional: noise reduction
try:
    import noisereduce as nr
    NOISE_REDUCE_AVAILABLE = True
except ImportError:
    NOISE_REDUCE_AVAILABLE = False

from elk.engine.pipeline.base_pipeline import BasePipeline
from elk.engine.schemas.interfaces import IncidentType, UrgencyLevel
from elk.engine.scoring import ConfidenceCalculator, ConfidenceResult
from elk.engine.rag import HybridRAG, VectorStore
from elk.engine.models import get_model_registry, get_transcription_cache
from ..data.lexicon import DAIRATE_BEJAIA, COMMUNES_FLAT, QUARTIERS_BEJAIA, VOCAB_MAP

from elk.engine.ai.llm import LLMClient
from elk.engine.schemas.interfaces import EmergencyCall, IncidentType, UrgencyLevel, Location

# Optimized French-style Béjaïa + Civil Protection vocabulary prompt
KABYLE_PROMPT_FRANCAIS = """
tilephon tilefonik telephone lmisaj message lprofni professeur
lbirou bureau lapolis police lhopital hopital sbitar
lambulance ambulance lipompier pompiers lprotection protection
laccident accident aksidan lasurance assurance
ladresse adresse lnumero numero lafich affiche
lvoiture voiture tomobil acamion camion lamoto moto
lbus bus ltrain train tamachint lgaraj agarage abrid route
lautoroute autoroute lastation station lkarfour carrefour
lvictime victime viktim lblessé blessé grave urgent danger
lurgence urgence lanfirmier infirmier ldocteur docteur tbib
lincendie incendie lehriq times nnoyade noyade gharq
leffondrement effondrement lexplosion explosion lasphyxie asphyxie
ssekour secours la3wana aide ssauvé sauvé
C'est urgent, yella lvictime, blessés graves g RN9.
Awi-d tilifunik, ad ceyy3egh lmisaj i lprofenat.
"""

class KabylePipeline(BasePipeline):
    """
    Specific implementation for decoding Mixed Kabyle/French emergency calls.
    Uses WhisperX for fast inference with word-level alignment.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.llm = LLMClient()
        self.enable_alignment = config.get("enable_alignment", True)
        
        # Initialize Confidence Calculator (FR-04)
        self.confidence_calculator = ConfidenceCalculator(
            asr_weight=config.get("confidence_asr_weight", 0.40),
            entity_weight=config.get("confidence_entity_weight", 0.35),
            rag_weight=config.get("confidence_rag_weight", 0.25)
        )
        
        # Initialize Hybrid RAG (FR-02)
        self._init_hybrid_rag(config)
        
        self._load_whisperx(config)
        if self.enable_alignment:
            self._load_alignment_model()

    def _load_whisperx(self, config: Dict[str, Any]):
        """
        Load WhisperX model using ModelRegistry (singleton).
        Prevents duplicate model loading across pipeline instances.
        """
        import whisperx
        import torch
        self.whisperx = whisperx
        
        # Model priority: local fine-tuned > config > default
        model_path = config.get("whisper_model", "whisper-kabyle-dgpc-v6-ct2")
        
        # Check for local fine-tuned model
        local_model_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..",
            "ml_pipeline", "whisper-kabyle-dgpc-v6-ct2"
        )
        if os.path.exists(local_model_path):
            model_path = local_model_path
            logger.info(f"Using fine-tuned WhisperX: {model_path}")
        
        # Device detection
        if torch.cuda.is_available():
            self.device = "cuda"
            compute_type = "int8_float16"  # Optimized: 75% faster
        else:
            self.device = "cpu"
            compute_type = "int8"
        
        # Use ModelRegistry singleton for caching
        registry = get_model_registry()
        self.model = registry.get_whisper_model(
            model_id=model_path,
            device=self.device,
            compute_type=compute_type,
            asr_options={
                "initial_prompt": KABYLE_PROMPT_FRANCAIS,
                "beam_size": 5,
                "temperatures": [0.0, 0.2, 0.4],
                "compression_ratio_threshold": 2.4,
                "no_speech_threshold": 0.6,
            }
        )
        
        # Get transcription cache for A2 optimization
        self._transcription_cache = get_transcription_cache()

    def _load_alignment_model(self):
        """
        Load word-level alignment model using ModelRegistry (singleton).
        """
        try:
            registry = get_model_registry()
            self.align_model, self.align_metadata = registry.get_alignment_model(
                language_code="fr",
                device=self.device
            )
        except Exception as e:
            logger.warning(f"Alignment unavailable: {e}")
            self.enable_alignment = False
    
    def cleanup_gpu_memory(self):
        """Free GPU memory when models are no longer needed."""
        import gc
        import torch
        
        if hasattr(self, 'model'):
            del self.model
        if hasattr(self, 'align_model'):
            del self.align_model
        
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("GPU memory cleared")

    def _init_hybrid_rag(self, config: Dict[str, Any]):
        """
        Initialize Hybrid RAG with vector + keyword search (FR-02).
        Uses ChromaDB for semantic search and lexicon for keyword matching.
        """
        enable_vector = config.get("enable_vector_rag", True)
        
        if enable_vector:
            try:
                # Create persistent vector store in pack directory
                pack_dir = os.path.dirname(__file__)
                persist_path = os.path.join(pack_dir, "..", ".chroma_db")
                
                vector_store = VectorStore(
                    collection_name="dz_kab_knowledge",
                    persist_path=persist_path
                )
                self.rag = HybridRAG(
                    vector_store=vector_store,
                    keyword_weight=config.get("rag_keyword_weight", 0.5),
                    vector_weight=config.get("rag_vector_weight", 0.5)
                )
            except Exception as e:
                logger.warning(f"Vector RAG init failed, using keyword-only: {e}")
                self.rag = HybridRAG(vector_store=None)
        else:
            logger.info("Using keyword-only RAG (vector disabled)")
            self.rag = HybridRAG(vector_store=None)
        
        # Load pack knowledge into RAG
        self.rag.load_pack_knowledge(
            communes=COMMUNES_FLAT,
            quartiers=QUARTIERS_BEJAIA,
            vocab=VOCAB_MAP
        )


    def transcribe(self, audio_path: str) -> str:
        """
        ASR transcription using WhisperX with:
        - TranscriptionCache (A2 optimization)
        - Preprocessing (noise reduction + normalization)
        - Batch inference
        - Word-level alignment (optional)
        """
        # A2 Optimization: Check cache first
        cached = self._transcription_cache.get(audio_path)
        if cached is not None:
            logger.debug("TranscriptionCache hit")
            return cached
        
        # Load audio with WhisperX
        audio = self.whisperx.load_audio(audio_path)
        
        # Preprocessing: noise reduction if available
        if NOISE_REDUCE_AVAILABLE:
            audio = nr.reduce_noise(y=audio, sr=16000, prop_decrease=0.8)
            audio = audio / (np.max(np.abs(audio)) + 1e-8)
        
        # Transcribe with WhisperX
        result = self.model.transcribe(audio, batch_size=16)
        
        # Word-level alignment (optional)
        if self.enable_alignment and result.get("segments"):
            try:
                aligned = self.whisperx.align(
                    result["segments"],
                    self.align_model,
                    self.align_metadata,
                    audio,
                    self.device
                )
                result = aligned
            except Exception as e:
                logger.warning(f"Alignment failed: {e}")
        
        # Assemble transcription
        transcription = " ".join([s["text"].strip() for s in result.get("segments", [])])
        
        # A2 Optimization: Cache result
        self._transcription_cache.set(audio_path, transcription)
        
        return transcription

    def normalize(self, raw_text: str) -> str:
        """Text normalization with Arabizi mapping and vocabulary standardization."""
        text = raw_text.lower()
        
        # Arabizi Mapping
        arabizi = {"3": "ɛ", "7": "ḥ", "9": "q", "5": "x", "8": "ɣ"}
        for k, v in arabizi.items():
            text = text.replace(k, v)
        
        # Vocabulary normalization (Kabyle -> French)
        for k, v in VOCAB_MAP.items():
            text = text.replace(k, v)
        
        return text.strip()

    def retrieve_context(self, text: str) -> str:
        """
        HYBRID RAG: Retrieves context using vector + keyword search (FR-02).
        Combines semantic similarity with exact keyword matching.
        """
        results, context = self.rag.search(text, n_results=10)
        
        # Cache results for confidence calculation
        self._last_rag_results = results
        
        return context

    def extract(self, normalized_text: str) -> Dict[str, Any]:
        """
        AI-Powered Extraction (Gemini 1.5 Flash)
        Uses RAG Context to guide the LLM.
        Applies real Confidence Calculator (FR-04) for human review triggering.
        """
        # 1. Retrieve Knowledge (RAG)
        context = self.retrieve_context(normalized_text)
        self._last_rag_context = context  # Store for confidence calculation
        
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
        - Do NOT include 'confidence' field - it will be calculated separately.
        """

        # 3. Generate (Real AI)
        try:
            data = self.llm.generate_structured(
                system_prompt=system_prompt,
                user_input=normalized_text,
                response_schema=EmergencyCall
            )
            # Strip fields that BasePipeline adds later
            if "audio_file" in data: del data["audio_file"]
            if "transcription_raw" in data: del data["transcription_raw"]
            
            # 4. Calculate REAL confidence (FR-04)
            confidence_result = self.confidence_calculator.calculate(
                transcription=normalized_text,
                extracted=data,
                rag_context=context
            )
            
            # Override LLM's confidence guess with real calculation
            data["confidence"] = confidence_result.overall
            
            # Set human review flags based on real scoring
            data["needs_human_review"] = confidence_result.triggers_human_review
            if confidence_result.triggers_human_review:
                data["human_review_reason"] = confidence_result.reasoning
            
            # Log confidence breakdown for debugging
            print(f"📊 Confidence: {confidence_result.overall:.2f} "
                  f"(ASR:{confidence_result.asr_score:.2f} "
                  f"Entity:{confidence_result.entity_score:.2f} "
                  f"RAG:{confidence_result.rag_score:.2f})")
            if confidence_result.triggers_human_review:
                print(f"   ⚠️ {confidence_result.reasoning}")
            
            return data
            
        except Exception as e:
            print(f"⚠️ AI Failure, falling back to rules: {e}")
            return {
                "incident_type": IncidentType.UNKNOWN,
                "urgency": UrgencyLevel.UNKNOWN,
                "confidence": 0.1,
                "needs_human_review": True,
                "human_review_reason": f"AI extraction failed: {str(e)}"
            }

