"""
ELK Connector Interface
Abstract base class for ERP/CRM integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseConnector(ABC):
    """
    Interface for pushing processed incidents to external systems.
    Implementations: MockERP, Webhook, Salesforce, etc.
    """
    
    @abstractmethod
    async def push_incident(self, incident_data: Dict[str, Any]) -> bool:
        """
        Push incident data to the external system.
        Returns True if successful, False otherwise.
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check connection to external system."""
        pass
