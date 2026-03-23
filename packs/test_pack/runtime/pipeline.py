"""
test-pack - Pipeline Implementation
"""

from typing import Any

from elk.kernel.ai.llm import LLMClient
from elk.kernel.pipeline.base_pipeline import BasePipeline
from elk.kernel.rag import HybridRAG
from elk.kernel.scoring import ConfidenceCalculator

from .data.lexicon import COMMUNES, QUARTIERS, VOCAB_MAP


class Pipeline(BasePipeline):
    """
    Language pack pipeline for test-pack.
    Implement the abstract methods.
    """

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.llm = LLMClient()

        # Initialize RAG and load pack knowledge
        self.rag = HybridRAG()
        self.rag.load_pack_knowledge(COMMUNES, QUARTIERS, VOCAB_MAP)

        # Initialize scoring calculator
        self.calculator = ConfidenceCalculator()

    def transcribe(self, audio_path: str) -> str:
        """Implement ASR transcription."""
        raise NotImplementedError("Implement transcribe()")

    def normalize(self, raw_text: str) -> str:
        """Implement text normalization."""
        return raw_text.lower().strip()

    def extract(self, normalized_text: str) -> dict[str, Any]:
        """Implement entity extraction."""
        raise NotImplementedError("Implement extract()")
