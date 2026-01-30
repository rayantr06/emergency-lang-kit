import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from .interfaces import OperationalState, SystemAction

class AnalyticsEngine:
    """
    The 'Memory' of the system.
    Responsible for structured logging and data warehousing.
    Enables Spatio-Temporal Analysis and Operational KPIs.
    """
    
    def __init__(self, storage_path: str = "data/warehouse"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Data Tables (JSONL)
        self.calls_log = self.storage_path / "calls_history.jsonl"
        self.decisions_log = self.storage_path / "decisions_history.jsonl"
        
    def log_call(self, state: OperationalState):
        """
        Logs the final operational state of a call.
        Used for: Incident Heatmaps, Peak Hour Analysis.
        """
        record = {
            "timestamp": state.timestamp.isoformat(),
            "call_id": state.call_id,
            "incident_type": state.incident_type.value,
            "urgency": state.urgency.value,
            "location": state.entities.location,
            "confidence": state.confidence_score,
            "validation_status": state.validation_status.value
        }
        
        self._append_to_log(self.calls_log, record)
        
    def log_decision(self, call_id: str, action: SystemAction):
        """
        Logs the system decision and action.
        Used for: Response Time Analysis, Resource Usage Stats.
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "call_id": call_id,
            "action_type": action.action_type,
            "target": action.target_resource,
            "payload": action.payload
        }
        
        self._append_to_log(self.decisions_log, record)
        
    def _append_to_log(self, file_path: Path, data: Dict[str, Any]):
        """Atomic append to JSONL file."""
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"⚠️ Analytics Error: Failed to write log to {file_path}: {e}")

    def get_daily_stats(self) -> Dict[str, Any]:
        """
        Example generic KPI calculator.
        """
        total_calls = 0
        incident_counts = {}
        
        if not self.calls_log.exists():
            return {"calls": 0}
            
        with open(self.calls_log, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    total_calls += 1
                    itype = data.get("incident_type", "unknown")
                    incident_counts[itype] = incident_counts.get(itype, 0) + 1
                except:
                    continue
                    
        return {
            "total_calls_24h": total_calls,
            "breakdown": incident_counts
        }
