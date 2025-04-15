# routes/health.py
from fastapi import APIRouter
from core.redis import redis_client

router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    try:
        pong = await redis_client.ping()
        redis_status = pong is True
    except Exception:
        redis_status = False

    return {
        "status": "ok",
        "redis": redis_status,
    }