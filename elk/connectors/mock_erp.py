"""
Mock ERP Connector
Simulates an Enterprise Resource Planning system by logging events to a local file.
Useful for demos and testing without external dependencies.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any
from elk.connectors.base import BaseConnector

logger = logging.getLogger(__name__)

class MockERPConnector(BaseConnector):
    def __init__(self, log_file: str = "mock_erp_events.jsonl"):
        self.log_file = log_file
        
    async def push_incident(self, incident_data: Dict[str, Any]) -> bool:
        """Simulate creating a ticket in the ERP."""
        payload = {
            "erp_timestamp": datetime.utcnow().isoformat(),
            "event": "INCIDENT_REPORT",
            "source": "ELK_AI_AGENT",
            "data": incident_data
        }
        
        try:
            # Atomic append (os agnostic enough for demo)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload) + "\n")
            
            logger.info(f"MockERP: Incident pushed to {self.log_file}")
            return True
        except Exception as e:
            logger.error(f"MockERP Push Failed: {e}")
            return False

    async def health_check(self) -> bool:
        return True
