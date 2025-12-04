"""Azure Blob Storage helpers."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone

from azure.storage.blob import (
    BlobServiceClient,
    ContentSettings,
    generate_blob_sas,
    BlobSasPermissions,
)
from azure.identity import DefaultAzureCredential

from .config import StorageConfig


def get_blob_service(storage: StorageConfig) -> BlobServiceClient:
    """Create a BlobServiceClient from storage configuration."""
    if storage.connection_string and storage.use_shared_key:
        return BlobServiceClient.from_connection_string(storage.connection_string)
    if storage.account_url:
        # Use Azure AD authentication (DefaultAzureCredential)
        credential = DefaultAzureCredential()
        return BlobServiceClient(account_url=storage.account_url, credential=credential)
    if storage.connection_string:
        # Extract account URL from connection string for Azure AD auth
        for part in storage.connection_string.split(";"):
            if part.startswith("AccountName="):
                account_name = part[len("AccountName="):]
                account_url = f"https://{account_name}.blob.core.windows.net"
                credential = DefaultAzureCredential()
                return BlobServiceClient(account_url=account_url, credential=credential)
    raise ValueError("StorageConfig requires either connection_string or account_url.")


def ensure_container(bsc: BlobServiceClient, container: str) -> None:
    """Ensure the container exists, creating it if necessary."""
    try:
        bsc.create_container(container)
    except Exception:
        # likely already exists
        pass


def _extract_account_key_from_connection_string(conn_str: str) -> str | None:
    """Extract account key from a connection string."""
    for part in conn_str.split(";"):
        if part.startswith("AccountKey="):
            return part[len("AccountKey="):]
    return None


def upload_and_sas_url(
    bsc: BlobServiceClient,
    container: str,
    name: str,
    data: bytes,
    content_type: str,
    sas_expiry_minutes: int,
    account_key: str | None = None,
) -> str:
    """
    Upload a blob and return a SAS URL for read access.
    
    If account_key is not provided, uses user delegation SAS with Azure AD credentials.
    
    Args:
        bsc: BlobServiceClient instance
        container: Container name
        name: Blob name
        data: Blob data bytes
        content_type: MIME content type
        sas_expiry_minutes: SAS token expiry in minutes
        account_key: Storage account key (optional - if not provided, uses user delegation SAS)
    """
    blob_client = bsc.get_blob_client(container, name)
    blob_client.upload_blob(
        data,
        overwrite=True,
        content_settings=ContentSettings(content_type=content_type),
    )

    # Generate read-only SAS for the individual blob
    parts = blob_client.url.split("/", 3)
    account_name = parts[2].split(".")[0]

    start_time = datetime.now(timezone.utc) - timedelta(minutes=5)  # 5 min buffer for clock skew
    expiry = datetime.now(timezone.utc) + timedelta(minutes=sas_expiry_minutes)

    if account_key:
        # Use account key for SAS generation
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container,
            blob_name=name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry,
        )
    else:
        # Use user delegation SAS (Azure AD authentication)
        from azure.storage.blob import generate_blob_sas, UserDelegationKey
        
        # Get user delegation key from Azure AD
        user_delegation_key = bsc.get_user_delegation_key(
            key_start_time=start_time,
            key_expiry_time=expiry,
        )
        
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container,
            blob_name=name,
            user_delegation_key=user_delegation_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry,
            start=start_time,
        )
    
    return f"{blob_client.url}?{sas_token}"
