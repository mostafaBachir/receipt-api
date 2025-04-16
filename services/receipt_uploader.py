# services/receipt_uploader.py

import os
import uuid
import mimetypes
from datetime import datetime, timezone, timedelta

from azure.storage.blob import generate_blob_sas, BlobSasPermissions, ContentSettings
from core.blob import get_container_client, get_sync_blob_service
from core.logger import get_logger
from core.config import AZURE_BLOB_CONTAINER
logger = get_logger("receipt-uploader")

def generate_blob_name(user_id: str, original_filename: str) -> str:
    ext = os.path.splitext(original_filename)[-1]
    today = datetime.now(timezone.utc).strftime("%Y-%m")
    unique_id = uuid.uuid4().hex[:12]
    return f"{user_id}/{today}/{unique_id}{ext}"

def generate_sas_url(blob_name: str, expiry_minutes: int = 180) -> str:
    logger.info(AZURE_BLOB_CONTAINER)
    blob_service = get_sync_blob_service()
    if blob_service is None:
        raise RuntimeError("❌ _blob_service non initialisé")

    sas_token = generate_blob_sas(
        account_name=blob_service.account_name,
        container_name=AZURE_BLOB_CONTAINER,
        blob_name=blob_name,
        account_key=blob_service.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes),
    )
    blob_url = f"https://{blob_service.account_name}.blob.core.windows.net/{AZURE_BLOB_CONTAINER}/{blob_name}"
    print(f"{blob_url}?{sas_token}")
    return f"{blob_url}?{sas_token}"

async def upload_receipt_to_blob(local_path: str, blob_name: str) -> str:
    logger.info(AZURE_BLOB_CONTAINER)
    try:
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"❌ Fichier introuvable : {local_path}")

        content_type, _ = mimetypes.guess_type(local_path)
        content_type = content_type or "application/octet-stream"

        container_client = await get_container_client()
        blob_client = container_client.get_blob_client(blob_name)

        with open(local_path, "rb") as data:
            await blob_client.upload_blob(data, overwrite=True,
                                          content_settings=ContentSettings(content_type=content_type))

        logger.info(f"✅ Blob uploadé : {blob_name} (type={content_type})")

        return generate_sas_url(blob_name)

    except Exception as e:
        logger.error(f"❌ Échec upload {blob_name} : {e}")
        raise RuntimeError(f"Erreur upload blob : {e}")

    finally:
        try:
            os.remove(local_path)
            logger.info(f"🧼 Fichier supprimé localement : {local_path}")
        except Exception as e:
            logger.warning(f"⚠️ Impossible de supprimer localement : {e}")
