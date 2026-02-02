"""
ELK Kernel - RAG Reranking
Cross-encoder reranking for improved retrieval precision.
Best practice from LangChain: rerank results before LLM context.
"""

import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class RankedResult:
    """A search result with relevance score."""
    document: str
    metadata: dict
    original_score: float
    rerank_score: Optional[float] = None
    
    @property
    def final_score(self) -> float:
        """Return rerank score if available, else original."""
        return self.rerank_score if self.rerank_score is not None else self.original_score


class CrossEncoderReranker:
    """
    Cross-encoder reranker for improved retrieval precision.
    
    Uses sentence-transformers cross-encoder models to rerank
    initial retrieval results based on query-document relevance.
    
    Best practice: Rerank top-K results (e.g., K=20) down to top-N (e.g., N=5).
    """
    
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: Optional[str] = None
    ):
        """
        Initialize cross-encoder.
        
        Args:
            model_name: HuggingFace model name for cross-encoder
            device: 'cuda', 'cpu', or None for auto-detect
        """
        self.model_name = model_name
        self.device = device
        self._model = None
    
    def _load_model(self):
        """Lazy load cross-encoder model."""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name, device=self.device)
                logger.info(f"Loaded reranker: {self.model_name}")
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed. Reranking disabled. "
                    "Install with: pip install sentence-transformers"
                )
                raise
        return self._model
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Rerank documents by relevance to query.
        
        Args:
            query: The search query
            documents: List of document texts to rerank
            top_n: Number of top results to return
            
        Returns:
            List of (document, score) tuples, sorted by relevance
        """
        if not documents:
            return []
        
        model = self._load_model()
        
        # Create query-document pairs
        pairs = [(query, doc) for doc in documents]
        
        # Get relevance scores
        scores = model.predict(pairs)
        
        # Sort by score descending
        scored_docs = sorted(
            zip(documents, scores),
            key=lambda x: x[1],
            reverse=True
        )
        
        return scored_docs[:top_n]
    
    def rerank_with_metadata(
        self,
        query: str,
        results: List[RankedResult],
        top_n: int = 5
    ) -> List[RankedResult]:
        """
        Rerank results preserving metadata.
        
        Args:
            query: The search query
            results: List of RankedResult objects
            top_n: Number of top results to return
            
        Returns:
            Reranked list of RankedResult objects
        """
        if not results:
            return []
        
        model = self._load_model()
        
        # Create query-document pairs
        pairs = [(query, r.document) for r in results]
        
        # Get relevance scores
        scores = model.predict(pairs)
        
        # Update rerank scores
        for result, score in zip(results, scores):
            result.rerank_score = float(score)
        
        # Sort by rerank score descending
        sorted_results = sorted(results, key=lambda r: r.final_score, reverse=True)
        
        return sorted_results[:top_n]


class MinScoreFilter:
    """
    Filter results below minimum relevance threshold.
    Best practice: Remove low-quality matches before LLM context.
    """
    
    def __init__(self, min_score: float = 0.3):
        self.min_score = min_score
    
    def filter(self, results: List[RankedResult]) -> List[RankedResult]:
        """Remove results below threshold."""
        return [r for r in results if r.final_score >= self.min_score]


def create_reranking_pipeline(
    use_reranker: bool = True,
    min_score: float = 0.3,
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
):
    """
    Factory function to create reranking pipeline.
    
    Args:
        use_reranker: Whether to use cross-encoder (requires sentence-transformers)
        min_score: Minimum score threshold
        rerank_model: Model name for cross-encoder
        
    Returns:
        Callable that takes (query, results) and returns filtered, reranked results
    """
    reranker = None
    if use_reranker:
        try:
            reranker = CrossEncoderReranker(model_name=rerank_model)
        except ImportError:
            logger.warning("Reranking disabled - sentence-transformers not available")
    
    score_filter = MinScoreFilter(min_score=min_score)
    
    def rerank_pipeline(
        query: str,
        results: List[RankedResult],
        top_n: int = 5
    ) -> List[RankedResult]:
        """Apply reranking and filtering pipeline."""
        
        if reranker:
            results = reranker.rerank_with_metadata(query, results, top_n=top_n * 2)
        
        results = score_filter.filter(results)
        
        return results[:top_n]
    
    return rerank_pipeline
