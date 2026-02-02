"""
ELK Kernel - Analytics & Audit Layer
Implements MASTER_VISION Part 5: Data Warehouse & Analytics

Features:
- JSONL logging for audit trail
- Call analytics and metrics
- Heatmap data generation
- KPI tracking
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class CallRecord:
    """Immutable record of a processed call for audit."""
    call_id: str
    timestamp: str
    audio_file: str
    pack: str
    
    # Pipeline outputs
    transcription_raw: str
    transcription_normalized: str
    incident_type: str
    urgency: str
    location: Dict[str, Any]
    
    # Confidence & Review
    confidence: float
    asr_confidence: Optional[float]
    entity_confidence: Optional[float]
    rag_confidence: Optional[float]
    needs_human_review: bool
    human_review_reason: Optional[str]
    
    # Processing metadata
    processing_time_ms: int
    llm_provider: str
    asr_model: str
    
    # Dispatch actions (if any)
    dispatch_action: Optional[str] = None
    dispatch_units: Optional[List[str]] = None


class AuditLogger:
    """
    JSONL-based audit logger for call processing.
    Writes immutable records for compliance and analysis.
    """
    
    def __init__(
        self,
        log_dir: str = "logs",
        filename_prefix: str = "calls"
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Daily log files
        today = datetime.now().strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"{filename_prefix}_{today}.jsonl"
        
        print(f"📊 Audit logging to: {self.log_file}")
    
    def log(self, record: CallRecord) -> None:
        """Append a call record to the JSONL log."""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(record), ensure_ascii=False) + '\n')
    
    def log_dict(self, data: Dict[str, Any]) -> None:
        """Log a raw dictionary (for flexibility)."""
        data['logged_at'] = datetime.now().isoformat()
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, default=str) + '\n')


class CallAnalytics:
    """
    Real-time analytics for emergency call processing.
    Tracks KPIs and generates reports.
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self._stats = {
            "total_calls": 0,
            "by_incident_type": {},
            "by_urgency": {},
            "by_commune": {},
            "avg_confidence": 0.0,
            "human_review_count": 0,
            "avg_processing_time_ms": 0.0
        }
    
    def record_call(
        self,
        incident_type: str,
        urgency: str,
        commune: Optional[str],
        confidence: float,
        needs_review: bool,
        processing_time_ms: int
    ):
        """Record a call for analytics."""
        total = self._stats["total_calls"]
        
        # Update counters
        self._stats["total_calls"] = total + 1
        
        # By incident type
        self._stats["by_incident_type"][incident_type] = \
            self._stats["by_incident_type"].get(incident_type, 0) + 1
        
        # By urgency
        self._stats["by_urgency"][urgency] = \
            self._stats["by_urgency"].get(urgency, 0) + 1
        
        # By commune
        if commune:
            self._stats["by_commune"][commune] = \
                self._stats["by_commune"].get(commune, 0) + 1
        
        # Running averages
        if total > 0:
            self._stats["avg_confidence"] = (
                (self._stats["avg_confidence"] * total + confidence) / (total + 1)
            )
            self._stats["avg_processing_time_ms"] = (
                (self._stats["avg_processing_time_ms"] * total + processing_time_ms) / (total + 1)
            )
        else:
            self._stats["avg_confidence"] = confidence
            self._stats["avg_processing_time_ms"] = float(processing_time_ms)
        
        # Human review
        if needs_review:
            self._stats["human_review_count"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current analytics stats."""
        stats = self._stats.copy()
        stats["human_review_rate"] = (
            self._stats["human_review_count"] / max(self._stats["total_calls"], 1)
        )
        return stats
    
    def get_kpis(self) -> Dict[str, Any]:
        """Get key performance indicators."""
        total = max(self._stats["total_calls"], 1)
        return {
            "total_processed": self._stats["total_calls"],
            "avg_confidence": round(self._stats["avg_confidence"], 3),
            "human_review_rate": round(self._stats["human_review_count"] / total, 3),
            "avg_response_time_ms": round(self._stats["avg_processing_time_ms"], 1),
            "top_incident_type": max(
                self._stats["by_incident_type"].items(),
                key=lambda x: x[1],
                default=("NONE", 0)
            )[0],
            "top_commune": max(
                self._stats["by_commune"].items(),
                key=lambda x: x[1],
                default=("UNKNOWN", 0)
            )[0]
        }
    
    def generate_heatmap_data(self) -> Dict[str, Any]:
        """Generate data for spatial heatmap visualization."""
        return {
            "type": "heatmap",
            "commune_counts": self._stats["by_commune"],
            "urgency_distribution": self._stats["by_urgency"],
            "generated_at": datetime.now().isoformat()
        }
    
    def load_from_logs(self, days: int = 7):
        """Load historical data from JSONL logs."""
        from datetime import timedelta
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            log_file = self.log_dir / f"calls_{date_str}.jsonl"
            
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            record = json.loads(line)
                            self.record_call(
                                incident_type=record.get("incident_type", "UNKNOWN"),
                                urgency=record.get("urgency", "UNKNOWN"),
                                commune=record.get("location", {}).get("commune"),
                                confidence=record.get("confidence", 0.0),
                                needs_review=record.get("needs_human_review", False),
                                processing_time_ms=record.get("processing_time_ms", 0)
                            )
                        except json.JSONDecodeError:
                            continue


class ProcessingTimer:
    """Context manager for timing pipeline processing."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.elapsed_ms = 0
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, *args):
        self.end_time = time.perf_counter()
        self.elapsed_ms = int((self.end_time - self.start_time) * 1000)
