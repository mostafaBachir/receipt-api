# core/blob.py

from azure.storage.blob.aio import BlobServiceClient, ContainerClient
from azure.storage.blob import BlobServiceClient as SyncBlobServiceClient
from core.config import AZURE_STORAGE_CONNECTION_STRING, AZURE_BLOB_CONTAINER

_blob_service: SyncBlobServiceClient | None = None
_async_blob_service: BlobServiceClient | None = None
_container_client: ContainerClient | None = None

async def init_blob_service():
    global _blob_service, _async_blob_service, _container_client

    if _blob_service is None:
        _blob_service = SyncBlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

    if _async_blob_service is None:
        _async_blob_service = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

    if _container_client is None:
        _container_client = _async_blob_service.get_container_client(AZURE_BLOB_CONTAINER)

def get_sync_blob_service():
    return _blob_service

async def get_container_client() -> ContainerClient:
    if _container_client is None:
        await init_blob_service()
    return _container_client
