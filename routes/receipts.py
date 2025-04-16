from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.concurrency import run_in_threadpool
from typing import List
import asyncio
from core.logger import get_logger
from services.receipt_processor import process_single_receipt
from PIL import Image, ImageEnhance
import io

router = APIRouter()
logger = get_logger("receipt-routes")

async def process_and_optimize_receipt(file: UploadFile):
    """Wrapper pour le traitement avec optimisation d'image"""
    try:
        # Optimisation pour les images avant traitement
        if file.content_type in ['image/jpeg', 'image/png']:
            image_data = await file.read()
            
            # Optimisation avec Pillow
            img = Image.open(io.BytesIO(image_data))
            if img.mode != 'L':
                img = img.convert('L')  # Conversion niveaux de gris
            if img.width > 1200:
                img = img.resize((1200, int(img.height * (1200/img.width))))
            img = ImageEnhance.Contrast(img).enhance(1.15)
            
            # Sauvegarde en mémoire
            optimized_buffer = io.BytesIO()
            img.save(optimized_buffer, format='JPEG', quality=85)
            optimized_buffer.seek(0)
            file.file = optimized_buffer
            
        return await process_single_receipt(file)
        
    except Exception as e:
        logger.error(f"Erreur optimisation/traitement {file.filename}", exc_info=True)
        raise

@router.post("/image/upload", tags=["Receipts"])
async def upload_receipts(files: List[UploadFile] = File(...)):
    """
    Traitement de reçus avec :
    - Optimisation automatique des images
    - Traitement parallèle
    - Gestion robuste des erreurs
    """
    tasks = []
    
    for file in files:
        try:
            # Validation basique du type de fichier
            if file.content_type not in ['image/jpeg', 'image/png', 'application/pdf']:
                raise HTTPException(400, detail=f"Type de fichier non supporté: {file.content_type}")
                
            tasks.append(process_and_optimize_receipt(file))
            
        except Exception as e:
            logger.error(f"Erreur pré-traitement {file.filename}", exc_info=True)
            tasks.append(asyncio.sleep(0))  # Placeholder pour garder l'ordre
            continue

    # Exécution en parallèle avec gestion des erreurs
    processed_results = []
    for i, task in enumerate(asyncio.as_completed(tasks)):
        try:
            result = await task
            processed_results.append(result)
        except Exception as e:
            file = files[i]
            processed_results.append({
                "filename": file.filename,
                "error": str(e),
                "success": False
            })
            logger.error(f"Échec traitement {file.filename}", exc_info=True)

    # Statistiques de traitement
    success_count = sum(1 for r in processed_results if isinstance(r, dict) and r.get("success", False))
    
    return {
        "processed": success_count,
        "failed": len(processed_results) - success_count,
        "results": processed_results
    }