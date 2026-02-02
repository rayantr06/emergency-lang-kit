"""
Connector Factory
Instantiates the appropriate connector based on configuration.
"""

import os
from elk.connectors.base import BaseConnector
from elk.connectors.mock_erp import MockERPConnector
from elk.connectors.webhook import WebhookConnector

class ConnectorFactory:
    @staticmethod
    def get_connector() -> BaseConnector:
        """Return configured connector instance."""
        conn_type = os.getenv("CONNECTOR_TYPE", "mock").lower()
        
        if conn_type == "webhook":
            return WebhookConnector()
        elif conn_type == "salesforce":
            # Future implementation
            raise NotImplementedError("Salesforce connector not implemented")
        else:
            return MockERPConnector()
