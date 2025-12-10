"""
Cache Storage Abstraction

Supports:
- Azure Blob Storage (for production/container deployments)
- Local filesystem (ONLY for local development/testing, disabled by default in production)

Security: Local storage is disabled when running in a container (WEBSITE_SITE_NAME env var present)
to prevent storing confidential data locally in the webapp.
"""
import os
import json
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


def is_running_in_container() -> bool:
    """Check if running in Azure Container App or App Service."""
    # Azure Container Apps and App Service set these env vars
    return bool(
        os.environ.get("WEBSITE_SITE_NAME") or 
        os.environ.get("CONTAINER_APP_NAME") or
        os.environ.get("RUNNING_IN_CONTAINER")
    )


class CacheStorage(ABC):
    """Abstract base class for cache storage backends."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached data by key. Returns None if not found."""
        pass
    
    @abstractmethod
    def set(self, key: str, data: Dict[str, Any]) -> None:
        """Store data with the given key."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a key from cache. Returns True if deleted."""
        pass
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the cache storage is available and usable."""
        pass


class NullCacheStorage(CacheStorage):
    """
    No-op cache storage that doesn't store anything.
    Used when caching is disabled or no storage backend is available.
    """
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        return None
    
    def set(self, key: str, data: Dict[str, Any]) -> None:
        pass  # No-op
    
    def exists(self, key: str) -> bool:
        return False
    
    def delete(self, key: str) -> bool:
        return False
    
    @property
    def is_available(self) -> bool:
        return False


class LocalCacheStorage(CacheStorage):
    """
    Local filesystem cache storage.
    
    WARNING: Only use for local development/testing.
    Disabled automatically when running in a container.
    """
    
    def __init__(self, cache_dir: str = ".extraction_cache"):
        self.cache_dir = cache_dir
        self._available = True
        
        # Security: Disable local storage in container environments or when Azure Storage is configured
        if is_running_in_container() or os.environ.get("AZURE_STORAGE_ACCOUNT_NAME"):
            print("[Cache] WARNING: Local cache disabled in container environment or when Azure Storage is configured for security")
            self._available = False
        else:
            os.makedirs(cache_dir, exist_ok=True)
    
    def _get_path(self, key: str) -> str:
        """Get full path for a cache key."""
        safe_key = key.replace("/", "_").replace("\\", "_")
        return os.path.join(self.cache_dir, f"{safe_key}.json")
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        if not self._available:
            return None
        path = self._get_path(key)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def set(self, key: str, data: Dict[str, Any]) -> None:
        if not self._available:
            return
        path = self._get_path(key)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def exists(self, key: str) -> bool:
        if not self._available:
            return False
        return os.path.exists(self._get_path(key))
    
    def delete(self, key: str) -> bool:
        if not self._available:
            return False
        path = self._get_path(key)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
    
    @property
    def is_available(self) -> bool:
        return self._available


class AzureBlobCacheStorage(CacheStorage):
    """Azure Blob Storage cache backend for production use."""
    
    def __init__(
        self,
        connection_string: Optional[str] = None,
        container_name: str = "extraction-cache",
        account_url: Optional[str] = None,
        credential: Optional[Any] = None
    ):
        self._available = False
        self.container_name = container_name
        self.container_client = None
        
        try:
            from azure.storage.blob import BlobServiceClient
        except ImportError:
            print("[Cache] azure-storage-blob not installed, Azure cache unavailable")
            return
        
        blob_service = None
        
        # Try connection string first
        if connection_string:
            blob_service = BlobServiceClient.from_connection_string(connection_string)
        elif account_url:
            if credential is None:
                from azure.identity import DefaultAzureCredential
                credential = DefaultAzureCredential()
            blob_service = BlobServiceClient(account_url=account_url, credential=credential)
        else:
            # Try environment variables
            conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
            if conn_str:
                blob_service = BlobServiceClient.from_connection_string(conn_str)
            else:
                account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
                if account_name:
                    try:
                        from azure.identity import DefaultAzureCredential
                        account_url = f"https://{account_name}.blob.core.windows.net"
                        blob_service = BlobServiceClient(
                            account_url=account_url,
                            credential=DefaultAzureCredential()
                        )
                    except Exception as e:
                        print(f"[Cache] Failed to connect with managed identity: {e}")
                        return
        
        if blob_service is None:
            return
        
        # Get or create container
        try:
            self.container_client = blob_service.get_container_client(container_name)
            try:
                self.container_client.get_container_properties()
            except Exception:
                self.container_client.create_container()
            self._available = True
        except Exception as e:
            print(f"[Cache] Failed to initialize Azure Blob container: {e}")
    
    def _get_blob_name(self, key: str) -> str:
        return f"{key}.json"
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        if not self._available or self.container_client is None:
            return None
        blob_name = self._get_blob_name(key)
        blob_client = self.container_client.get_blob_client(blob_name)
        try:
            download = blob_client.download_blob()
            content = download.readall().decode("utf-8")
            return json.loads(content)
        except Exception:
            return None
    
    def set(self, key: str, data: Dict[str, Any]) -> None:
        if not self._available or self.container_client is None:
            return
        blob_name = self._get_blob_name(key)
        blob_client = self.container_client.get_blob_client(blob_name)
        content = json.dumps(data, indent=2, ensure_ascii=False)
        blob_client.upload_blob(content.encode("utf-8"), overwrite=True)
    
    def exists(self, key: str) -> bool:
        if not self._available or self.container_client is None:
            return False
        blob_name = self._get_blob_name(key)
        blob_client = self.container_client.get_blob_client(blob_name)
        return blob_client.exists()
    
    def delete(self, key: str) -> bool:
        if not self._available or self.container_client is None:
            return False
        blob_name = self._get_blob_name(key)
        blob_client = self.container_client.get_blob_client(blob_name)
        try:
            blob_client.delete_blob()
            return True
        except Exception:
            return False
    
    @property
    def is_available(self) -> bool:
        return self._available


# Global cache storage instance
_cache_storage: Optional[CacheStorage] = None


def get_cache_storage(
    allow_local: bool = False,
    blob_container: str = "extraction-cache",
    verbose: bool = True
) -> CacheStorage:
    """
    Get the cache storage backend.
    
    Priority:
    1. Azure Blob Storage (if credentials available)
    2. Local filesystem (if allow_local=True and not in container)
    3. NullCacheStorage (no caching)
    
    Args:
        allow_local: Allow local filesystem cache (only for development)
        blob_container: Azure blob container name
        verbose: Print status messages
    
    Returns:
        CacheStorage instance
    """
    global _cache_storage
    
    if _cache_storage is not None:
        return _cache_storage
    
    in_container = is_running_in_container()
    
    # Try Azure Blob Storage first
    has_azure_storage = bool(
        os.environ.get("AZURE_STORAGE_CONNECTION_STRING") or
        os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
    )
    
    if has_azure_storage:
        try:
            storage = AzureBlobCacheStorage(container_name=blob_container)
            if storage.is_available:
                if verbose:
                    print("[Cache] Using Azure Blob Storage")
                _cache_storage = storage
                return storage
        except Exception as e:
            if verbose:
                print(f"[Cache] Azure Blob Storage failed: {e}")
    
    # In container without Azure storage = no caching
    if in_container:
        if verbose:
            print("[Cache] No Azure Storage configured - caching disabled in container")
        _cache_storage = NullCacheStorage()
        return _cache_storage
    
    # Local development: allow local cache if explicitly enabled
    if allow_local:
        if verbose:
            print("[Cache] Using local filesystem cache (development only)")
        _cache_storage = LocalCacheStorage()
        return _cache_storage
    
    # Default: no caching
    if verbose:
        print("[Cache] Caching disabled (use --allow-local-cache for development)")
    _cache_storage = NullCacheStorage()
    return _cache_storage


def reset_cache_storage():
    """Reset the global cache storage instance (for testing)."""
    global _cache_storage
    _cache_storage = None


def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file for cache key generation."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_cache_key(file_hash: str, prefix: str = "", **kwargs) -> str:
    """
    Generate a cache key from file hash and additional parameters.
    
    Args:
        file_hash: SHA256 hash of the source file
        prefix: Optional prefix (e.g., "pptx", "xlsx")
        **kwargs: Additional parameters to include in key
    
    Returns:
        Cache key string
    """
    parts = [prefix] if prefix else []
    parts.append(file_hash)
    
    for key in sorted(kwargs.keys()):
        value = kwargs[key]
        parts.append(f"{key}_{value}")
    
    return "_".join(parts)
