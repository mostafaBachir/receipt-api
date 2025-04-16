import os
import shutil
import io
from datetime import datetime
from fastapi import UploadFile, HTTPException
from PIL import Image, ImageEnhance
from services.parser import parse_receipt_with_retries
from services.vision_parser import parse_receipt_with_gpt
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

async def optimize_image(file_contents: bytes) -> bytes:
    """Optimise l'image pour l'OCR"""
    img = Image.open(io.BytesIO(file_contents))
    
    # Conversion en niveaux de gris si ce n'est pas un PDF
    if img.mode != 'L':
        img = img.convert('L')
    
    # Redimensionnement (max 1200px de large)
    if img.width > 1200:
        ratio = 1200 / img.width
        img = img.resize((1200, int(img.height * ratio)))
    
    # Ajustement du contraste
    img = ImageEnhance.Contrast(img).enhance(1.15)
    
    output_buffer = io.BytesIO()
    img.save(output_buffer, format='JPEG', quality=85, optimize=True)
    return output_buffer.getvalue()

async def process_single_receipt(file: UploadFile, parse: str = "gpt"):
    """
    Processus optimisé :
    1. Vérification du type MIME
    2. Prétraitement de l'image (si JPEG/PNG)
    3. Sauvegarde temporaire
    4. Parsing avec retry
    5. Nettoyage
    """
    content_type = file.content_type
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(400, detail=f"Type non supporté : {content_type}")

    try:
        # Lecture du fichier
        file_contents = await file.read()
        
        # Optimisation pour les images (sauf PDF)
        if content_type != "application/pdf":
            file_contents = await optimize_image(file_contents)

        # Sauvegarde temporaire
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        local_filename = f"{timestamp}_{os.urandom(4).hex()}{ALLOWED_TYPES[content_type]}"
        local_path = os.path.join(UPLOAD_DIR, local_filename)
        
        with open(local_path, "wb") as buffer:
            buffer.write(file_contents)

        # Parsing
        parser_map = {
            "gpt": parse_receipt_with_gpt,
            "xai": globals().get("parse_receipt_with_xai")
        }
        
        if parse not in parser_map or not parser_map[parse]:
            raise HTTPException(400, detail=f"Parseur inconnu : {parse}")

        parse_task = create_task(
            parse_receipt_with_retries(local_path, parser_map[parse])
        )
        parsed_result = await gather(parse_task)
        
        return {
            "id": str(uuid4()),
            "filename": file.filename,
            "optimized_filename": local_filename,
            "size_original": len(file_contents),
            "summary": parsed_result[0].get("summary"),
            "parsed": parsed_result[0].get("data"),
            "parser": parse,
            "success": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur traitement reçu {file.filename}: {str(e)}", exc_info=True)
        return {
            "filename": file.filename,
            "error": str(e),
            "success": False
        }
    finally:
        if 'local_path' in locals() and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception as e:
                logger.warning(f"Échec suppression {local_path}: {str(e)}")