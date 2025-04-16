from motor.motor_asyncio import AsyncIOMotorClient
from core.config import MONGO_DB_STRING, MONGO_DB_NAME
from core.logger import get_logger

logger = get_logger("mongo")

try:
    client = AsyncIOMotorClient(MONGO_DB_STRING)
    db = client[MONGO_DB_NAME]
    expenses_collection = db["receipts"]

    logger.info(f"✅ Connexion MongoDB établie à DB = {MONGO_DB_NAME}")
except Exception as e:
    logger.error(f"❌ Échec connexion MongoDB : {e}")
    raise e
