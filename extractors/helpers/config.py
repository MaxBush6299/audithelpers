"""Configuration dataclasses for PPTX extraction."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from azure.ai.documentintelligence import DocumentIntelligenceClient


@dataclass
class StorageConfig:
    """Azure Blob Storage configuration."""
    connection_string: Optional[str] = None  # If provided, we'll use it
    account_url: Optional[str] = None        # OR use account_url + sas/auth in env
    account_key: Optional[str] = None        # Required for SAS generation (if using shared key)
    container: str = "pptx-tmp"
    sas_expiry_minutes: int = 15
    use_shared_key: bool = False             # Set to False to use Azure AD auth instead

    def get_account_key(self) -> Optional[str]:
        """Extract account key from connection string or return explicit key."""
        if not self.use_shared_key:
            return None  # Don't use shared key, will use user delegation SAS
        if self.account_key:
            return self.account_key
        if self.connection_string:
            for part in self.connection_string.split(";"):
                if part.startswith("AccountKey="):
                    return part[len("AccountKey="):]
        return None


@dataclass
class DIConfig:
    """Azure Document Intelligence configuration."""
    endpoint: str                            # e.g., "https://<your-di>.cognitiveservices.azure.com"
    key: str                                 # API key
    model_id: str = "prebuilt-layout"        # Options: prebuilt-layout, prebuilt-read, prebuilt-document

    def get_client(self) -> "DocumentIntelligenceClient":
        """Create a Document Intelligence client."""
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        from azure.core.credentials import AzureKeyCredential
        return DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key)
        )


# Legacy: Keep CUConfig for backward compatibility but mark as deprecated
@dataclass
class CUConfig:
    """Azure Content Understanding configuration (deprecated - use DIConfig)."""
    endpoint: str                            # e.g., "https://<your-cu>.cognitiveservices.azure.com"
    key: str                                 # Ocp-Apim-Subscription-Key
    api_version: str = "2025-11-01"          # keep configurable to avoid hard-coding
    analyzer: str = "prebuilt-layout"        # "prebuilt-read" or "prebuilt-layout"
    poll_interval_seconds: float = 1.2
    timeout_seconds: int = 120
