"""
Webhook Connector
Pushes incidents to a configured HTTP endpoint (e.g., Zapier, n8n, Custom API).
"""

import os
import httpx
import logging
from typing import Dict, Any
from elk.connectors.base import BaseConnector

logger = logging.getLogger(__name__)

class WebhookConnector(BaseConnector):
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.getenv("WEBHOOK_URL")
        
    async def push_incident(self, incident_data: Dict[str, Any]) -> bool:
        if not self.webhook_url:
            logger.warning("WebhookConnector: No URL configured.")
            return False
            
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=incident_data,
                    headers={"User-Agent": "ELK-AI-Agent/0.2.0"}
                )
                response.raise_for_status()
                logger.info(f"Webhook pushed to {self.webhook_url} (Region: {incident_data.get('region', 'unknown')})")
                return True
        except Exception as e:
            logger.error(f"Webhook Push Failed: {e}")
            return False

    async def health_check(self) -> bool:
        if not self.webhook_url:
            return False
        # Simple ping or check logic could go here
        return True
