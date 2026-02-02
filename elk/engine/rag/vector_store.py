"""
ELK Kernel - Vector RAG Store
Implements FR-02: Context-Aware Extraction (RAG)

Features:
- Vector search using ChromaDB
- Hybrid search: BM25 (keyword) + Vector (semantic)
- Persistent storage for knowledge packs
- Auto-indexing from lexicon and geography data
- LRU caching for repeated queries
"""

import os
import re
import logging
from functools import lru_cache
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RAGResult:
    """Single RAG retrieval result."""
    text: str
    score: float
    metadata: Dict[str, Any]
    source: str  # "vector" or "keyword"


class VectorStore:
    """
    ChromaDB-based vector store for semantic search.
    Stores embeddings for locations, vocabulary, and procedures.
    """
    
    def __init__(
        self,
        collection_name: str = "elk_knowledge",
        persist_path: Optional[str] = None
    ):
        import chromadb
        
        self.collection_name = collection_name
        
        # Use persistent storage if path provided
        if persist_path:
            os.makedirs(persist_path, exist_ok=True)
            self.client = chromadb.PersistentClient(path=persist_path)
            logger.info(f"ChromaDB persisting to: {persist_path}")
        else:
            self.client = chromadb.Client()
            logger.info("ChromaDB in-memory mode")
        
        # Get or create collection (auto-embeds with default model)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        
        logger.info(f"Collection '{collection_name}' ready ({self.collection.count()} docs)")
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> int:
        """
        Add documents to the vector store.
        Embeddings are generated automatically by ChromaDB.
        """
        if not documents:
            return 0
        
        # Generate IDs if not provided
        if ids is None:
            existing = self.collection.count()
            ids = [f"doc_{existing + i}" for i in range(len(documents))]
        
        # Default metadata if not provided
        if metadatas is None:
            metadatas = [{"source": "unknown"} for _ in documents]
        
        # Add to collection
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        return len(documents)
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[RAGResult]:
        """
        Semantic search in vector store.
        Returns top-k most similar documents.
        """
        if self.collection.count() == 0:
            return []
        
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results, self.collection.count()),
            where=filter_metadata,
            include=["documents", "distances", "metadatas"]
        )
        
        rag_results = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                distance = results["distances"][0][i] if results["distances"] else 1.0
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                
                # Convert distance to similarity score (cosine distance: 0=identical, 2=opposite)
                score = max(0, 1 - (distance / 2))
                
                rag_results.append(RAGResult(
                    text=doc,
                    score=score,
                    metadata=metadata,
                    source="vector"
                ))
        
        return rag_results
    
    def index_lexicon(
        self,
        communes: List[str],
        quartiers: List[str],
        vocab: Dict[str, str]
    ) -> int:
        """Index location and vocabulary data from pack lexicon."""
        docs = []
        metas = []
        ids = []
        
        # Index communes
        for i, commune in enumerate(communes):
            docs.append(f"Commune de Bejaia: {commune}")
            metas.append({"type": "commune", "name": commune})
            ids.append(f"commune_{i}")
        
        # Index quartiers
        for i, quartier in enumerate(quartiers):
            docs.append(f"Quartier connu de Bejaia: {quartier}")
            metas.append({"type": "quartier", "name": quartier})
            ids.append(f"quartier_{i}")
        
        # Index vocabulary mappings
        for i, (kabyle, french) in enumerate(vocab.items()):
            docs.append(f"Vocabulaire Kabyle: {kabyle} signifie {french}")
            metas.append({"type": "vocab", "kabyle": kabyle, "french": french})
            ids.append(f"vocab_{i}")
        
        if docs:
            self.collection.add(documents=docs, metadatas=metas, ids=ids)
        
        return len(docs)


class HybridRAG:
    """
    Hybrid RAG: Combines BM25 keyword search with vector semantic search.
    
    Per MASTER_VISION.md:
    - BM25 for exact matches (street names, proper nouns)
    - Vector for semantic similarity
    - Weighted combination of results
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        keyword_weight: float = 0.4,
        vector_weight: float = 0.6
    ):
        self.vector_store = vector_store
        self.keyword_weight = keyword_weight
        self.vector_weight = vector_weight
        
        # Keyword knowledge base (loaded from pack)
        self._communes: List[str] = []
        self._quartiers: List[str] = []
        self._vocab: Dict[str, str] = {}
    
    def load_pack_knowledge(
        self,
        communes: List[str],
        quartiers: List[str],
        vocab: Dict[str, str]
    ):
        """Load knowledge from language pack."""
        # Use tuples for hashability (enables caching)
        self._communes = tuple(c.lower() for c in communes)
        self._quartiers = tuple(q.lower() for q in quartiers)
        self._vocab = {k.lower(): v for k, v in vocab.items()}
        self._vocab_frozen = tuple(sorted(self._vocab.items()))
        
        # Clear keyword cache when knowledge changes
        self._keyword_search_cached.cache_clear()
        
        # Index into vector store if available
        if self.vector_store:
            count = self.vector_store.index_lexicon(communes, quartiers, vocab)
            logger.info(f"Indexed {count} items into vector store")
    
    @lru_cache(maxsize=256)
    def _keyword_search_cached(self, text_lower: str, _communes_hash: int, _vocab_hash: int) -> tuple:
        """
        Cached keyword search (internal).
        Hash params ensure cache invalidation on knowledge change.
        """
        results = []
        
        # Match communes (exact substring)
        for commune in self._communes:
            if commune in text_lower:
                results.append((commune, 'commune', 1.0))
        
        # Match quartiers
        for quartier in self._quartiers:
            if quartier in text_lower:
                results.append((quartier, 'quartier', 1.0))
        
        # Match vocabulary
        for kabyle, french in self._vocab.items():
            if kabyle in text_lower:
                results.append((kabyle, 'vocab', 0.9, french))
        
        return tuple(results)
    
    def keyword_search(self, text: str) -> List[RAGResult]:
        """
        BM25-style keyword matching with LRU cache.
        Essential for exact matches on proper nouns.
        """
        text_lower = text.lower()
        
        # Use cached search with hash keys for cache invalidation
        cached = self._keyword_search_cached(
            text_lower, 
            hash(self._communes), 
            hash(self._vocab_frozen) if hasattr(self, '_vocab_frozen') else 0
        )
        
        # Convert cached tuples back to RAGResult objects
        results = []
        for item in cached:
            if item[1] == 'commune':
                results.append(RAGResult(
                    text=f"DETECTED_LOCATION: {item[0].title()} (Commune de Bejaia)",
                    score=item[2],
                    metadata={"type": "commune", "name": item[0]},
                    source="keyword"
                ))
            elif item[1] == 'quartier':
                results.append(RAGResult(
                    text=f"DETECTED_LANDMARK: {item[0].title()} (Quartier connu)",
                    score=item[2],
                    metadata={"type": "quartier", "name": item[0]},
                    source="keyword"
                ))
            elif item[1] == 'vocab':
                results.append(RAGResult(
                    text=f"DETECTED_VOCAB: {item[0]} -> {item[3]}",
                    score=item[2],
                    metadata={"type": "vocab", "kabyle": item[0], "french": item[3]},
                    source="keyword"
                ))
        
        return results
    
    def search(
        self,
        query: str,
        n_results: int = 10
    ) -> Tuple[List[RAGResult], str]:
        """
        Hybrid search: keyword + vector combined.
        
        Returns:
            Tuple of (results list, formatted context string)
        """
        all_results = []
        
        # 1. Keyword search (exact matches)
        keyword_results = self.keyword_search(query)
        for r in keyword_results:
            r.score *= self.keyword_weight
        all_results.extend(keyword_results)
        
        # 2. Vector search (semantic)
        if self.vector_store and self.vector_store.collection.count() > 0:
            vector_results = self.vector_store.query(query, n_results=n_results)
            for r in vector_results:
                r.score *= self.vector_weight
            all_results.extend(vector_results)
        
        # Deduplicate and sort by score
        seen = set()
        unique_results = []
        for r in sorted(all_results, key=lambda x: x.score, reverse=True):
            key = r.text[:50]  # Dedup key
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
        
        # Format context string
        if not unique_results:
            context = "NO_CONTEXT_FOUND"
        else:
            context_lines = [r.text for r in unique_results[:n_results]]
            context = "\n".join(context_lines)
        
        return unique_results[:n_results], context
