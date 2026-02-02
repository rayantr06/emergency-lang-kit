"""
ELK CLI - Factory Tools
Implements MASTER_VISION Part 4: scaffold, train, extract, package
"""

import os
import sys
import argparse
from pathlib import Path


def scaffold(args):
    """
    Create a new language pack with standard structure.
    Implements: elk scaffold <pack-name> [--domain] [--language]
    """
    pack_name = args.name.replace("-", "_")
    base_dir = Path(args.output or "packs") / pack_name
    
    if base_dir.exists() and not args.force:
        print(f"❌ Pack already exists: {base_dir}")
        print("   Use --force to overwrite")
        return 1
    
    # Create directory structure (MASTER_VISION 3.1)
    dirs = [
        base_dir,
        base_dir / "data",
        base_dir / "runtime",
        base_dir / "prompts",
        base_dir / "models",
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created: {d}")
    
    # Create config.yaml
    config_content = f'''# {args.name} Pack Configuration
pack:
  name: "{args.name}"
  version: "0.1.0"
  language: "{args.language or 'und'}"
  domain: "{args.domain or 'general'}"

llm:
  provider: "${{LLM_PROVIDER:-gemini}}"
  cloud:
    model: "gemini-1.5-flash"
    api_key: "${{GEMINI_API_KEY}}"
  local:
    model: "${{OLLAMA_MODEL:-llama3}}"
    base_url: "${{OLLAMA_BASE_URL:-http://localhost:11434}}"

asr:
  model: "${{WHISPER_MODEL:-small}}"
  enable_alignment: true

rag:
  enable_vector: true
  keyword_weight: 0.5
  vector_weight: 0.5

confidence:
  asr_weight: 0.40
  entity_weight: 0.35
  rag_weight: 0.25
  human_review_threshold: 0.70
'''
    (base_dir / "config.yaml").write_text(config_content, encoding='utf-8')
    print(f"📝 Created: {base_dir / 'config.yaml'}")
    
    # Create __init__.py files
    (base_dir / "__init__.py").write_text(f'# {args.name} Pack\\n', encoding='utf-8')
    (base_dir / "data" / "__init__.py").write_text('# Data module\\n', encoding='utf-8')
    (base_dir / "runtime" / "__init__.py").write_text('# Runtime module\\n', encoding='utf-8')
    (base_dir / "prompts" / "__init__.py").write_text('# Prompts module\\n', encoding='utf-8')
    
    # Create skeleton lexicon.py
    lexicon_content = f'''"""
{args.name} - Lexicon
Vocabulary mappings and location data.
"""

# Vocabulary: Local Language -> Standard
VOCAB_MAP = {{
    # Add your mappings here
    # "local_word": "standard_word",
}}

# Communes/Regions
COMMUNES = [
    # Add your communes here
]

# Landmarks/Quartiers
QUARTIERS = [
    # Add your landmarks here
]
'''
    (base_dir / "data" / "lexicon.py").write_text(lexicon_content, encoding='utf-8')
    print(f"📝 Created: {base_dir / 'data' / 'lexicon.py'}")
    
    # Create skeleton pipeline.py
    pipeline_content = f'''"""
{args.name} - Pipeline Implementation
"""

from typing import Dict, Any
from elk.kernel.pipeline.base_pipeline import BasePipeline
from elk.kernel.ai.llm import LLMClient
from elk.kernel.scoring import ConfidenceCalculator
from elk.kernel.rag import HybridRAG
from .data.lexicon import VOCAB_MAP, COMMUNES, QUARTIERS


class Pipeline(BasePipeline):
    """
    Language pack pipeline for {args.name}.
    Implement the abstract methods.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.llm = LLMClient()
        # TODO: Initialize ASR, RAG, etc.
    
    def transcribe(self, audio_path: str) -> str:
        """Implement ASR transcription."""
        raise NotImplementedError("Implement transcribe()")
    
    def normalize(self, raw_text: str) -> str:
        """Implement text normalization."""
        return raw_text.lower().strip()
    
    def extract(self, normalized_text: str) -> Dict[str, Any]:
        """Implement entity extraction."""
        raise NotImplementedError("Implement extract()")
'''
    (base_dir / "runtime" / "pipeline.py").write_text(pipeline_content, encoding='utf-8')
    print(f"📝 Created: {base_dir / 'runtime' / 'pipeline.py'}")
    
    # Create extraction prompt
    prompt_content = f'''# {args.name} - Extraction Prompt

You are an AI assistant for extracting structured data from transcribed calls.

## Context
Domain: {args.domain or 'general'}
Language: {args.language or 'undefined'}

## Output Schema
Return valid JSON matching the EmergencyCall schema:
- incident_type: Type of incident
- urgency: LOW, MEDIUM, HIGH, CRITICAL
- location: {{ commune, details, coordinates }}
- description: Brief summary

## Rules
1. Use ONLY information from the transcript
2. When uncertain, set needs_human_review to true
3. Preserve original language for quoted speech
'''
    (base_dir / "prompts" / "extraction.md").write_text(prompt_content, encoding='utf-8')
    print(f"📝 Created: {base_dir / 'prompts' / 'extraction.md'}")
    
    print(f"\n✅ Pack scaffolded: {base_dir}")
    print(f"   Next steps:")
    print(f"   1. Edit data/lexicon.py with your vocabulary")
    print(f"   2. Implement runtime/pipeline.py")
    print(f"   3. Customize prompts/extraction.md")
    
    return 0


def train(args):
    """
    Train/fine-tune models for a pack.
    Implements: elk train <pack-name> [--dataset] [--model]
    Per MASTER_VISION 4.4: Unsloth QLoRA training.
    """
    print(f"🚂 Training pack: {args.pack}")
    print(f"   Dataset: {args.dataset}")
    print(f"   Base model: {args.model}")
    print(f"   Epochs: {args.epochs}")
    
    # Verify dataset exists
    if not os.path.exists(args.dataset):
        print(f"❌ Dataset not found: {args.dataset}")
        return 1
    
    # Check if trainer dependencies exist
    try:
        from elk.training import TrainingDatabase, UnslothTrainer, TrainingConfig, LoRAConfig
        print("✅ Training modules loaded")
    except ImportError as e:
        print(f"❌ Training dependencies not installed: {e}")
        print("   Install: pip install unsloth peft transformers datasets")
        return 1
    
    try:
        # If JSONL, import into database first
        if args.dataset.endswith('.jsonl'):
            print("\n📊 Importing dataset to training database...")
            db = TrainingDatabase(f"{args.pack}_training.db")
            count = db.import_from_jsonl(args.dataset)
            print(f"   Imported: {count} samples")
            
            # Export for training
            train_path, test_path = db.export_for_training("./training_data")
            print(f"   Train set: {train_path}")
            print(f"   Test set: {test_path}")
            db.close()
        else:
            train_path = args.dataset
            test_path = None
        
        # Configure training
        config = TrainingConfig(
            base_model=args.model,
            output_dir=f"./packs/{args.pack.replace('-', '_')}/models/training_output",
            num_epochs=args.epochs,
            lora=LoRAConfig(r=16, lora_alpha=32)
        )
        
        print("\n🏋️ Starting training...")
        print(f"   Model: {config.base_model}")
        print(f"   LoRA r={config.lora.r}, alpha={config.lora.lora_alpha}")
        
        # Train
        trainer = UnslothTrainer(config)
        trainer.load_model()
        trainer.prepare_dataset(train_path, test_path)
        metrics = trainer.train()
        
        # Save adapter
        pack_path = f"./packs/{args.pack.replace('-', '_')}"
        adapter_path = trainer.save_adapter(pack_path)
        
        print(f"\n✅ Training complete!")
        print(f"   Loss: {metrics.get('loss', 'N/A')}")
        print(f"   Adapter saved: {adapter_path}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def extract(args):
    """
    Extract vocabulary from PDF/documents.
    Implements: elk extract <input-pdf> [--output]
    Per MASTER_VISION 4.2: Knowledge Refinery.
    """
    print(f"📄 Extracting from: {args.input}")
    
    if not os.path.exists(args.input):
        print(f"❌ File not found: {args.input}")
        return 1
    
    # Check dependencies
    try:
        from elk.factory.extractor import KnowledgeExtractor, PDFChunker
        print("✅ Extractor modules loaded")
    except ImportError as e:
        print(f"❌ Extraction dependencies not installed: {e}")
        print("   Install: pip install pymupdf pyyaml")
        return 1
    
    try:
        # Determine output directory
        output_dir = args.output or os.path.dirname(args.input) or "."
        
        print(f"   Output: {output_dir}")
        print(f"   LLM: {'ollama (local)' if args.local else 'gemini (cloud)'}")
        
        # Extract
        if args.local:
            os.environ['LLM_PROVIDER'] = 'ollama'
        
        extractor = KnowledgeExtractor()
        result = extractor.extract_from_pdf(args.input, output_dir)
        
        print(f"\n✅ Extraction complete!")
        print(f"   Vocabulary: {len(result.vocabulary)} terms")
        print(f"   Entities: {len(result.entities)} items")
        print(f"   Rules: {len(result.rules)} rules")
        print(f"\n📁 Output files:")
        print(f"   - {output_dir}/lexicon_candidate.yaml")
        print(f"   - {output_dir}/rules_candidate.yaml")
        print(f"\n⚠️  Review candidates before using in pack!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def package(args):
    """
    Package a pack for distribution.
    Implements: elk package <pack-name> [--output]
    """
    pack_name = args.pack.replace("-", "_")
    pack_dir = Path("packs") / pack_name
    
    if not pack_dir.exists():
        print(f"❌ Pack not found: {pack_dir}")
        return 1
    
    import shutil
    import json
    from datetime import datetime
    
    output = args.output or f"{args.pack}-{datetime.now().strftime('%Y%m%d')}.tar.gz"
    
    # Create manifest
    manifest = {
        "name": args.pack,
        "packaged": datetime.now().isoformat(),
        "files": []
    }
    
    for f in pack_dir.rglob("*"):
        if f.is_file() and "__pycache__" not in str(f):
            manifest["files"].append(str(f.relative_to(pack_dir)))
    
    manifest_file = pack_dir / "MANIFEST.json"
    manifest_file.write_text(json.dumps(manifest, indent=2))
    
    # Create tarball
    shutil.make_archive(
        output.replace(".tar.gz", ""),
        "gztar",
        "packs",
        pack_name
    )
    
    print(f"📦 Packaged: {output}")
    print(f"   Files: {len(manifest['files'])}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="elk",
        description="Emergency Lang Kit - Factory Tools"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # scaffold
    scaffold_parser = subparsers.add_parser("scaffold", help="Create new language pack")
    scaffold_parser.add_argument("name", help="Pack name (e.g., my-language)")
    scaffold_parser.add_argument("--domain", help="Domain (e.g., civil_protection, medical)")
    scaffold_parser.add_argument("--language", help="Language code (e.g., fr, kab)")
    scaffold_parser.add_argument("--output", help="Output directory")
    scaffold_parser.add_argument("--force", action="store_true", help="Overwrite existing")
    scaffold_parser.set_defaults(func=scaffold)
    
    # train
    train_parser = subparsers.add_parser("train", help="Fine-tune models for a pack")
    train_parser.add_argument("pack", help="Pack name")
    train_parser.add_argument("--dataset", required=True, help="Training dataset path (JSONL)")
    train_parser.add_argument("--model", default="openai/whisper-large-v3", help="Base model")
    train_parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    train_parser.set_defaults(func=train)
    
    # extract
    extract_parser = subparsers.add_parser("extract", help="Extract vocabulary from documents")
    extract_parser.add_argument("input", help="Input PDF/document path")
    extract_parser.add_argument("--output", help="Output directory for YAML files")
    extract_parser.add_argument("--local", action="store_true", help="Use local LLM (Ollama)")
    extract_parser.set_defaults(func=extract)
    
    # package
    package_parser = subparsers.add_parser("package", help="Package a pack for distribution")
    package_parser.add_argument("pack", help="Pack name")
    package_parser.add_argument("--output", help="Output file path")
    package_parser.set_defaults(func=package)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
