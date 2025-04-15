from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.logger import get_logger
from security.jwt import decode_jwt

security = HTTPBearer()
logger = get_logger("auth-deps")

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    token = credentials.credentials
    try:
        payload = decode_jwt(token)
        user_id = payload.get("user_id") or payload.get("sub")
        if not user_id:
            raise ValueError("Token missing user_id")

        logger.info(f"🔐 Utilisateur identifié : {user_id}")
        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role"),
        }

    except Exception as e:
        logger.warning(f"❌ Erreur auth : {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
