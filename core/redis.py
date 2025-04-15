import redis.asyncio as redis
from core.config import REDIS_URL
from core.logger import get_logger

logger = get_logger("redis")

# ✅ Connexion avec chaîne complète + timeouts
redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_timeout=5,               # Timeout sur lecture/écriture (sec)
    socket_connect_timeout=5        # Timeout initial de connexion
)

# 🧪 Ping (à appeler au démarrage si souhaité)
async def test_redis_connection():
    try:
        pong = await redis_client.ping()
        if pong:
            logger.info("✅ Connexion Redis OK")
        else:
            logger.warning("⚠️ Réponse inattendue de Redis (pas de PONG)")
    except Exception as e:
        logger.warning(f"❌ Échec de ping Redis : {e}")
