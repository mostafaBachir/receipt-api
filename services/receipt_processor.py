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

UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Type de fichier non supporté: {file.content_type}"
        )

    try:
        # Génération d'un nom de fichier unique
        file_id = str(uuid4())
        extension = ALLOWED_TYPES[file.content_type]
        temp_path = os.path.join(UPLOAD_DIR, f"{file_id}{extension}")
        
        # Lecture et optimisation du fichier
        file_contents = await file.read()
        if file.content_type in ['image/jpeg', 'image/png']:
            file_contents = await optimize_image(file_contents)
        
        # Sauvegarde temporaire
        with open(temp_path, "wb") as temp_file:
            temp_file.write(file_contents)
        
        # Parsing avec le bon service
        if parse == "gpt":
            result = await parse_receipt_with_gpt(temp_path)
        else:
            result = await parse_receipt_with_retries(temp_path)
            
        # Nettoyage
        os.remove(temp_path)
        
        return {
            "filename": file.filename,
            "parsed_data": result,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Erreur traitement {file.filename}", exc_info=True)
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement: {str(e)}"
        )