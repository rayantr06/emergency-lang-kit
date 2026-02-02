"""
ELK Training - Dataset Management
SQLite-based training database with versioning.
Per MASTER_VISION 4.5: Training Database.
"""

import os
import json
import hashlib
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class TrainingSample:
    """A single training sample for ASR fine-tuning."""
    audio_hash: str  # SHA256 of audio file
    audio_path: str
    transcription_raw: str
    transcription_golden: str  # Human validated
    dialect_tags: List[str]
    is_test_set: bool = False
    quality_score: float = 1.0
    created_at: str = ""
    validated_by: str = ""


class TrainingDatabase:
    """
    SQLite-based training data management.
    Avoids catastrophic forgetting via structured versioning.
    """
    
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS samples (
        audio_hash TEXT PRIMARY KEY,
        audio_path TEXT NOT NULL,
        transcription_raw TEXT,
        transcription_golden TEXT NOT NULL,
        dialect_tags TEXT,
        is_test_set INTEGER DEFAULT 0,
        quality_score REAL DEFAULT 1.0,
        created_at TEXT,
        validated_by TEXT
    );
    
    CREATE TABLE IF NOT EXISTS training_runs (
        run_id TEXT PRIMARY KEY,
        started_at TEXT,
        completed_at TEXT,
        samples_used INTEGER,
        base_model TEXT,
        lora_config TEXT,
        metrics TEXT,
        output_path TEXT
    );
    
    CREATE INDEX IF NOT EXISTS idx_test_set ON samples(is_test_set);
    CREATE INDEX IF NOT EXISTS idx_quality ON samples(quality_score);
    """
    
    def __init__(self, db_path: str = "training.db"):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
    
    def _init_schema(self):
        """Initialize database schema."""
        self.conn.executescript(self.SCHEMA)
        self.conn.commit()
    
    @staticmethod
    def compute_audio_hash(audio_path: str) -> str:
        """Compute SHA256 hash of audio file."""
        with open(audio_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    
    def add_sample(self, sample: TrainingSample) -> bool:
        """Add or update a training sample."""
        try:
            self.conn.execute("""
                INSERT OR REPLACE INTO samples 
                (audio_hash, audio_path, transcription_raw, transcription_golden,
                 dialect_tags, is_test_set, quality_score, created_at, validated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sample.audio_hash,
                sample.audio_path,
                sample.transcription_raw,
                sample.transcription_golden,
                json.dumps(sample.dialect_tags),
                1 if sample.is_test_set else 0,
                sample.quality_score,
                sample.created_at or datetime.now().isoformat(),
                sample.validated_by
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding sample: {e}")
            return False
    
    def get_training_set(
        self,
        min_quality: float = 0.5,
        limit: Optional[int] = None
    ) -> List[TrainingSample]:
        """Get training samples (is_test_set=False)."""
        query = """
            SELECT * FROM samples 
            WHERE is_test_set = 0 AND quality_score >= ?
            ORDER BY quality_score DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self.conn.execute(query, (min_quality,))
        return [self._row_to_sample(row) for row in cursor.fetchall()]
    
    def get_test_set(self) -> List[TrainingSample]:
        """Get test samples (is_test_set=True)."""
        cursor = self.conn.execute(
            "SELECT * FROM samples WHERE is_test_set = 1"
        )
        return [self._row_to_sample(row) for row in cursor.fetchall()]
    
    def _row_to_sample(self, row: sqlite3.Row) -> TrainingSample:
        """Convert database row to TrainingSample."""
        return TrainingSample(
            audio_hash=row['audio_hash'],
            audio_path=row['audio_path'],
            transcription_raw=row['transcription_raw'] or "",
            transcription_golden=row['transcription_golden'],
            dialect_tags=json.loads(row['dialect_tags'] or '[]'),
            is_test_set=bool(row['is_test_set']),
            quality_score=row['quality_score'],
            created_at=row['created_at'] or "",
            validated_by=row['validated_by'] or ""
        )
    
    def import_from_jsonl(self, jsonl_path: str) -> int:
        """Import samples from JSONL file (from elk annotate)."""
        imported = 0
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    sample = TrainingSample(
                        audio_hash=data.get('audio_hash') or self.compute_audio_hash(data['audio_path']),
                        audio_path=data['audio_path'],
                        transcription_raw=data.get('transcription_raw', ''),
                        transcription_golden=data['transcription'],
                        dialect_tags=data.get('dialect_tags', []),
                        is_test_set=data.get('is_test_set', False),
                        quality_score=data.get('quality_score', 1.0),
                        validated_by=data.get('validated_by', 'unknown')
                    )
                    if self.add_sample(sample):
                        imported += 1
                except Exception as e:
                    print(f"Skipping invalid line: {e}")
        
        return imported
    
    def export_for_training(
        self,
        output_path: str,
        test_split: float = 0.2
    ) -> Tuple[str, str]:
        """
        Export training and test sets to JSONL files.
        Returns (train_path, test_path).
        """
        import random
        
        samples = self.get_training_set()
        random.shuffle(samples)
        
        split_idx = int(len(samples) * (1 - test_split))
        train_samples = samples[:split_idx]
        test_samples = samples[split_idx:]
        
        # Mark test samples
        for sample in test_samples:
            sample.is_test_set = True
            self.add_sample(sample)
        
        train_path = Path(output_path) / "train.jsonl"
        test_path = Path(output_path) / "test.jsonl"
        
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        with open(train_path, 'w', encoding='utf-8') as f:
            for s in train_samples:
                f.write(json.dumps({
                    'audio': s.audio_path,
                    'sentence': s.transcription_golden
                }) + '\n')
        
        with open(test_path, 'w', encoding='utf-8') as f:
            for s in test_samples:
                f.write(json.dumps({
                    'audio': s.audio_path,
                    'sentence': s.transcription_golden
                }) + '\n')
        
        return str(train_path), str(test_path)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_test_set = 0 THEN 1 ELSE 0 END) as train_count,
                SUM(CASE WHEN is_test_set = 1 THEN 1 ELSE 0 END) as test_count,
                AVG(quality_score) as avg_quality
            FROM samples
        """)
        row = cursor.fetchone()
        return {
            'total_samples': row['total'],
            'train_samples': row['train_count'],
            'test_samples': row['test_count'],
            'avg_quality': round(row['avg_quality'] or 0, 3)
        }
    
    def close(self):
        """Close database connection."""
        self.conn.close()
