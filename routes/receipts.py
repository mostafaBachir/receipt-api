from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body, Path,Request
from datetime import datetime
from typing import List
from security.dependencies import get_current_user
from models.expense import ReceiptModel, ReceiptUpdateModel  # si séparé

from core.logger import get_logger
from core.mongo import expenses_collection
from services.receipt_processor import process_single_receipt
from pymongo.errors import DuplicateKeyError
from typing import Optional
from bson import ObjectId
import json

router = APIRouter()
logger = get_logger("receipt-routes")

router = APIRouter()

@router.post("/receipts/image/check", tags=["Receipts"])
async def check_image_exists(
    original_signature: str = Body(...),
    optimized_signature: Optional[str] = Body(None),
    user=Depends(get_current_user)
):
    """
    Vérifie si une image a déjà été enregistrée par l'utilisateur
    à partir de sa signature (originale ou optimisée).
    """
    query = {
        "user_id": user["user_id"],
        "$or": [
            {"original_signature": original_signature},
            {"optimized_signature": optimized_signature} if optimized_signature else {}
        ]
    }

    # Nettoie la requête si pas de optimized_signature
    if not optimized_signature:
        query["$or"] = [query["$or"][0]]

    match = await expenses_collection.find_one(query)

    return {
        "exists": match is not None,
        "receipt_id": str(match["_id"]) if match else None,
        "merchant": match.get("merchant") if match else None,
        "summary": match.get("summary") if match else None
    }

@router.post("/receipts/image/upload", tags=["Receipts"])
async def upload_receipts(
    files: list[UploadFile] = File(...),
    user=Depends(get_current_user)
):
    results = []

    for file in files:
        try:
            result = await process_single_receipt(file, user)
            results.append(result)
        except Exception as e:
            logger.error(f"❌ Erreur traitement fichier {file.filename} : {e}")
            results.append({
                "filename": file.filename,
                "error": str(e)
            })
    logger.info(results)
    return {
        "message": f"{len(results)} fichier(s) traité(s)",
        "results": results
    }

@router.post("/receipts", tags=["Receipts"])
async def create_receipts(
    receipts: List[ReceiptModel],
    user=Depends(get_current_user)
):
    inserted_ids = []
    duplicates = []

    for r in receipts:
        if r.user_id != user["user_id"]:
            raise HTTPException(
                status_code=403,
                detail="Reçu assigné à un autre utilisateur"
            )

        r_dict = r.dict()
        r_dict.pop("id", None)
        try:
            result = await expenses_collection.insert_one(r_dict)
            inserted_ids.append(str(result.inserted_id))
        except DuplicateKeyError:
            logger.warning(f"🔁 Doublon détecté pour la signature: {r_dict.get('original_signature')}")
            duplicates.append(r_dict.get("original_signature"))
        except Exception as e:
            logger.error(f"❌ Erreur insertion reçu: {e}")
            raise HTTPException(status_code=500, detail="Erreur serveur interne")

    response = {
        "inserted": len(inserted_ids),
        "inserted_ids": inserted_ids,
    }

    if duplicates:
        response["duplicates"] = duplicates
        response["message"] = f"{len(duplicates)} doublon(s) ignoré(s), {len(inserted_ids)} reçu(s) ajouté(s)."
    else:
        response["message"] = f"{len(inserted_ids)} reçu(s) ajouté(s)."

    return response

from fastapi import Query

@router.get("/receipts", tags=["Receipts"])
async def get_user_receipts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    user=Depends(get_current_user)
):
    try:
        skip = (page - 1) * limit

        total_count = await expenses_collection.count_documents({"user_id": str(user["user_id"])})
        cursor = (
            expenses_collection
            .find({"user_id": str(user["user_id"])})
            .sort("timestamp", -1)
            .skip(skip)
            .limit(limit)
        )

        receipts = await cursor.to_list(length=limit)
        for r in receipts:
            r["id"] = str(r.pop("_id"))

        return {
            "receipts": receipts,
            "totalCount": total_count,
            "page": page,
            "limit": limit
        }

    except Exception as e:
        logger.error(f"❌ Erreur récupération reçus: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des reçus")



@router.put("/receipts/{receipt_id}", tags=["Receipts"])
async def update_receipt(
    receipt_id: str,
    updated_data: ReceiptUpdateModel = Body(...),
    user=Depends(get_current_user)
):
    logger.info(f"📥 Mise à jour reçue : {updated_data.dict()}")
    if updated_data.user_id and updated_data.user_id != str(user["user_id"]):
        raise HTTPException(status_code=403, detail="Reçu non autorisé pour cet utilisateur")

    try:
        result = await expenses_collection.update_one(
            {"_id": ObjectId(receipt_id), "user_id": str(user["user_id"])},
            {"$set": updated_data.dict(exclude_unset=True)}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Aucune mise à jour effectuée.")

        updated = await expenses_collection.find_one({"_id": ObjectId(receipt_id)})
        updated["id"] = str(updated.pop("_id"))
        return updated

    except Exception as e:
        logger.error(f"❌ Erreur update reçu : {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")

@router.delete("/receipts/{receipt_id}", tags=["Receipts"])
async def delete_receipt(
    receipt_id: str = Path(..., title="ID du reçu à supprimer"),
    user=Depends(get_current_user)
):
    """
    Supprime un reçu appartenant à l'utilisateur.
    """
    try:
        result = await expenses_collection.delete_one({
            "_id": ObjectId(receipt_id),
            "user_id": user["user_id"]
        })

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Reçu non trouvé ou déjà supprimé.")

        return {
            "message": "🗑️ Reçu supprimé avec succès",
            "receipt_id": receipt_id
        }

    except Exception as e:
        logger.error(f"❌ Erreur suppression reçu {receipt_id} : {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression du reçu")

@router.put("/receipts/{receipt_id}/debug", tags=["Receipts"])
async def debug_receipt_update(
    receipt_id: str,
    request: Request,
    user=Depends(get_current_user)
):
    body = await request.json()
    logger.info(f"📥 Reçu brut pour debug :\n{json.dumps(body, indent=2, ensure_ascii=False)}")
    return body
