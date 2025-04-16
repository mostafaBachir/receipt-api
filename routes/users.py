from fastapi import APIRouter, Depends
from security.dependencies import get_current_user
from datetime import datetime

router = APIRouter()

@router.get("/me", tags=["User"])
async def get_current_user_info(user=Depends(get_current_user)):
    exp = user.get("exp")
    exp_date = datetime.fromtimestamp(exp).isoformat() if exp else None

    return {
        "user_id": user.get("user_id"),
        "email": user.get("email"),
        "role": user.get("role"),
        "permissions": user.get("permissions", []),
        "expires_at": exp_date
    }