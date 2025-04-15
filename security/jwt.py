from jose import JWTError, ExpiredSignatureError, jwt
from fastapi import HTTPException, status
from core.config import SECRET_KEY, ALGORITHM

# 🔓 Décode un JWT et lève une erreur si invalide ou expiré
def decode_jwt(token: str):
    print(f"📦 SECRET_KEY = {SECRET_KEY}")
    print(f"📜 Token = {token}")
    try:
        return jwt.decode(token, SECRET_KEY.encode(), algorithms=[ALGORITHM])
    
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expiré ⌛",
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ❌",
        )
