import os
import shutil
from datetime import datetime
from fastapi import UploadFile, HTTPException
from services.parser import parse_receipt_with_retries
from services.vision_parser import parse_receipt_with_gpt
from services.receipt_uploader import generate_blob_name, upload_receipt_to_blob
from core.logger import get_logger
from asyncio import create_task, gather
from uuid import uuid4
logger = get_logger("receipt-processor")

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf"
}

UPLOAD_DIR = "uploads"

async def process_single_receipt(file: UploadFile, user: dict, parse: str = "gpt"):
    """
    1. Vérifie le type MIME
    2. Sauvegarde temporairement le fichier en local
    3. Parse avec GPT ou XAI (avec retry intégré)
    4. Upload vers Azure Blob Storage (en parallèle ou seul)
    5. Supprime le fichier local
    6. Retourne le résumé + données parsées (optionnel)
    """
    content_type = file.content_type
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Type non supporté : {content_type}"
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_hex = os.urandom(4).hex()
    extension = ALLOWED_TYPES[content_type]
    local_filename = f"{timestamp}_{random_hex}{extension}"
    local_path = os.path.join(UPLOAD_DIR, local_filename)
    print(file.filename)
    with open(local_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        blob_name = generate_blob_name(str(user["user_id"]), file.filename)

        upload_task = create_task(upload_receipt_to_blob(local_path, blob_name))

        if parse == "gpt":
            parse_task = create_task(parse_receipt_with_retries(local_path, parse_receipt_with_gpt))
        elif parse == "xai":
            from services.vision_parser import parse_receipt_with_xai
            parse_task = create_task(parse_receipt_with_xai(local_path))
        else:
            parse_task = None

        if parse_task:
            parsed, blob_url = await gather(parse_task, upload_task)
        else:
            blob_url = await upload_task
            parsed = {}

        return {
            "id": str(uuid4()),  # 👈 identifiant unique pour ce reçu
            "filename": local_filename,
            "blob_url": blob_url,
            "summary": parsed.get("summary") if parsed else None,
            "parsed": parsed.get("data") if parsed else None,
            "parser": parse or None,
            "success": True,
        }

    except Exception as e:
        logger.error(f"❌ Erreur traitement reçu : {e}")
        return {
            "filename": local_filename,
            "error": str(e),
            "success": False,
        }

    finally:
        try:
            os.remove(local_path)
        except Exception as e:
            logger.warning(f"⚠️ Suppression fichier local échouée : {e}")
