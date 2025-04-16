# services/parser.py

import logging
from typing import Callable, Union
import asyncio
import os
import time
from core.logger import get_logger

logger = get_logger("parser")

def is_valid_parsing(parsed: dict) -> bool:
    """
    Vérifie si le parsing GPT retourne au moins un reçu structuré.
    Accepte soit une liste, soit un seul reçu.
    """
    data = parsed.get("data")
    if not data:
        return False

    if isinstance(data, list):
        return all("merchant_name" in r for r in data)
    if isinstance(data, dict):
        return "merchant_name" in data

    return False


async def parse_receipt_with_retries(file_path: str, parser_func, max_retries: int = 3, delay: float = 1.5):
    """
    Appelle le parser_func (GPT, XAI, etc.) avec gestion automatique des retries.
    Supprime le fichier en toute fin (même en cas d'échec).
    """
    parsed = None
    try:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔁 [GPT] Tentative {attempt} pour parser {file_path}")
                parsed = await parser_func(file_path)
                return parsed
            except Exception as e:
                logger.error(f"❌ [GPT] Erreur tentative {attempt} : {e}")
                if attempt < max_retries:
                    await asyncio.sleep(delay)
                else:
                    logger.error("💥 Toutes les tentatives ont échoué")
                    return None
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"🧼 Fichier supprimé localement après toutes les tentatives : {file_path}")
            except Exception as e:
                logger.warning(f"⚠️ Suppression fichier local échouée : {e}")
