# services/redis_listener.py

import asyncio
import json
from core.redis import redis_client
from core.logger import get_logger

CHANNEL = "permissions:update"
RETRY_DELAY = 5
logger = get_logger("redis-listener")

async def listen_to_permission_events():
    while True:
        try:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(CHANNEL)
            logger.info(f"🔌 Abonné au canal Redis : {CHANNEL}")

            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=10)

                if message is None:
                    continue  # Pas de message, on continue l’écoute tranquille

                try:
                    event = json.loads(message["data"])
                    event_type = event.get("type")
                    user_id = event.get("user_id")

                    logger.info(f"📥 Event reçu → type: {event_type}, user_id: {user_id}")
                    # TODO : agir selon le type d'event

                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Données Redis non JSON : {message['data']}")

        except Exception as e:
            logger.error(f"❌ Erreur Redis : {e}")
            logger.info(f"⏳ Reconnexion dans {RETRY_DELAY}s…")
            await asyncio.sleep(RETRY_DELAY)
