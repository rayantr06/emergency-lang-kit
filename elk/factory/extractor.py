"""
ELK Factory - PDF Knowledge Extractor
Per MASTER_VISION 4.2: elk extract command.

Workflow:
1. PDF → Chunks (text extraction)
2. Chunks → LLM Extraction (entities, rules)
3. LLM Output → Candidate YAML
4. Human Review → Final rules.yaml/lexicon.yaml
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class ExtractedChunk:
    """A chunk of text extracted from PDF."""
    text: str
    page_number: int
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """Results from LLM extraction."""
    entities: List[Dict[str, str]]  # {"term": "...", "type": "location|vocab|rule"}
    rules: List[Dict[str, Any]]  # {"condition": "...", "action": "..."}
    vocabulary: Dict[str, str]  # {"local_term": "standard_term"}
    source_file: str
    confidence: float


class PDFChunker:
    """
    Extract and chunk text from PDF documents.
    Uses PyMuPDF (fitz) for reliable extraction.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def extract(self, pdf_path: str) -> List[ExtractedChunk]:
        """Extract text chunks from PDF."""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "PyMuPDF required for PDF extraction. "
                "Install with: pip install pymupdf"
            )
        
        chunks = []
        doc = fitz.open(pdf_path)
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            
            # Split into chunks with overlap
            page_chunks = self._chunk_text(text, page_num)
            chunks.extend(page_chunks)
        
        doc.close()
        
        logger.info(f"Extracted {len(chunks)} chunks from {pdf_path}")
        return chunks
    
    def _chunk_text(self, text: str, page_num: int) -> List[ExtractedChunk]:
        """Split text into overlapping chunks."""
        chunks = []
        
        if len(text) <= self.chunk_size:
            chunks.append(ExtractedChunk(
                text=text.strip(),
                page_number=page_num + 1,
                chunk_index=0
            ))
            return chunks
        
        start = 0
        chunk_idx = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Find paragraph boundary if possible
            if end < len(text):
                paragraph_end = text.rfind('\n\n', start, end)
                if paragraph_end > start:
                    end = paragraph_end
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(ExtractedChunk(
                    text=chunk_text,
                    page_number=page_num + 1,
                    chunk_index=chunk_idx
                ))
                chunk_idx += 1
            
            start = end - self.chunk_overlap
            if start < 0:
                start = end
        
        return chunks


class KnowledgeExtractor:
    """
    LLM-based knowledge extraction from document chunks.
    Extracts entities, rules, and vocabulary.
    """
    
    EXTRACTION_PROMPT = """You are a knowledge extraction system for emergency services.
Analyze the following text from a procedures manual and extract:

1. **VOCABULARY**: Local terms and their standard equivalents
   Format: {"local_term": "standard_term"}

2. **ENTITIES**: Named entities (locations, equipment, procedures)
   Format: [{"term": "...", "type": "location|equipment|procedure|personnel"}]

3. **RULES**: Business rules or dispatch logic
   Format: [{"condition": "IF ...", "action": "THEN ...", "priority": "HIGH|MEDIUM|LOW"}]

TEXT TO ANALYZE:
---
{chunk_text}
---

Respond with valid JSON only:
{{
    "vocabulary": {{}},
    "entities": [],
    "rules": []
}}
"""
    
    def __init__(self, llm_client=None):
        if llm_client is None:
            from elk.kernel.ai.llm import LLMClient
            self.llm = LLMClient()
        else:
            self.llm = llm_client
    
    def extract_from_chunk(self, chunk: ExtractedChunk) -> Dict[str, Any]:
        """Extract knowledge from a single chunk."""
        prompt = self.EXTRACTION_PROMPT.format(chunk_text=chunk.text)
        
        try:
            result = self.llm.extract_json(prompt)
            return {
                'vocabulary': result.get('vocabulary', {}),
                'entities': result.get('entities', []),
                'rules': result.get('rules', []),
                'page': chunk.page_number,
                'chunk': chunk.chunk_index
            }
        except Exception as e:
            logger.warning(f"Extraction failed for chunk {chunk.chunk_index}: {e}")
            return {'vocabulary': {}, 'entities': [], 'rules': []}
    
    def extract_from_pdf(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None
    ) -> ExtractionResult:
        """
        Full extraction pipeline: PDF → Chunks → LLM → Result.
        """
        # Chunk PDF
        chunker = PDFChunker()
        chunks = chunker.extract(pdf_path)
        
        # Extract from each chunk
        all_vocab = {}
        all_entities = []
        all_rules = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            result = self.extract_from_chunk(chunk)
            
            all_vocab.update(result.get('vocabulary', {}))
            all_entities.extend(result.get('entities', []))
            all_rules.extend(result.get('rules', []))
        
        # Deduplicate
        unique_entities = self._deduplicate_entities(all_entities)
        unique_rules = self._deduplicate_rules(all_rules)
        
        result = ExtractionResult(
            entities=unique_entities,
            rules=unique_rules,
            vocabulary=all_vocab,
            source_file=pdf_path,
            confidence=0.7  # Default, needs human review
        )
        
        # Save if output dir specified
        if output_dir:
            self._save_results(result, output_dir)
        
        return result
    
    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """Remove duplicate entities."""
        seen = set()
        unique = []
        for e in entities:
            key = (e.get('term', '').lower(), e.get('type', ''))
            if key not in seen:
                seen.add(key)
                unique.append(e)
        return unique
    
    def _deduplicate_rules(self, rules: List[Dict]) -> List[Dict]:
        """Remove duplicate rules."""
        seen = set()
        unique = []
        for r in rules:
            key = (r.get('condition', ''), r.get('action', ''))
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique
    
    def _save_results(self, result: ExtractionResult, output_dir: str):
        """Save extraction results as YAML candidates."""
        import yaml
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save vocabulary as lexicon_candidate.yaml
        lexicon_path = output_path / "lexicon_candidate.yaml"
        with open(lexicon_path, 'w', encoding='utf-8') as f:
            yaml.dump({
                'vocabulary': result.vocabulary,
                'source': result.source_file,
                'status': 'CANDIDATE_NEEDS_REVIEW'
            }, f, allow_unicode=True, default_flow_style=False)
        
        # Save rules as rules_candidate.yaml
        rules_path = output_path / "rules_candidate.yaml"
        with open(rules_path, 'w', encoding='utf-8') as f:
            yaml.dump({
                'entities': result.entities,
                'rules': result.rules,
                'source': result.source_file,
                'status': 'CANDIDATE_NEEDS_REVIEW'
            }, f, allow_unicode=True, default_flow_style=False)
        
        logger.info(f"Saved candidates to: {output_dir}")
        logger.info(f"  - {lexicon_path.name}: {len(result.vocabulary)} terms")
        logger.info(f"  - {rules_path.name}: {len(result.rules)} rules, {len(result.entities)} entities")


def extract_from_pdf(
    pdf_path: str,
    output_dir: str,
    use_local_llm: bool = False
) -> ExtractionResult:
    """
    High-level function for elk extract command.
    """
    if use_local_llm:
        os.environ['LLM_PROVIDER'] = 'ollama'
    
    extractor = KnowledgeExtractor()
    return extractor.extract_from_pdf(pdf_path, output_dir)
