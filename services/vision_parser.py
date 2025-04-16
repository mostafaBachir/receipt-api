import os
import base64
import mimetypes
import json
import tempfile
from openai import AsyncOpenAI
from pdf2image import convert_from_path
from core.config import OPENAI_API_KEY, PROMPT,DEBUG_GPT_PARSER,DEBUG_XAI_PARSER
from core.logger import get_logger

logger = get_logger("vision-parser")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

def encode_image_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def convert_pdf_to_image(pdf_path: str) -> str:
    images = convert_from_path(pdf_path, dpi=200, first_page=1, last_page=1)
    temp_img_path = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False).name
    images[0].save(temp_img_path, "JPEG")
    return temp_img_path

async def parse_receipt_with_gpt(file_path: str, debug: bool = DEBUG_GPT_PARSER) -> dict:
    try:
        mime_type, _ = mimetypes.guess_type(file_path)
        is_pdf = mime_type == "application/pdf"

        if is_pdf:
            logger.info("📄 PDF détecté → conversion en image")
            image_path = convert_pdf_to_image(file_path)
            mime_type = "image/jpeg"
        else:
            if not mime_type or not mime_type.startswith("image/"):
                raise ValueError("❌ Format non supporté (seules les images et PDF sont autorisés)")
            image_path = file_path

        image_data = encode_image_to_base64(image_path)

        prompt = PROMPT

        logger.info(f"📤 Envoi à GPT-4 Turbo Vision ({mime_type})")

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=800,
        )

        raw_output = response.choices[0].message.content.strip()
        if debug:
            print("🧪 Réponse GPT brute:\n", raw_output)

        logger.debug(f"🧾 Réponse brute GPT:\n{raw_output}")

        try:
            parsed = json.loads(raw_output)
            logger.info("json traité")
            logger.info(parsed)

            # Remap vers format ReceiptModel
            raw = parsed
            data = raw.get("data", {})
            items = data.get("items", [])

            mapped_items = []
            for item in items:
                mapped_items.append({
                    "name": item.get("name"),
                    "unit_price": item.get("unit_price"),
                    "quantite": item.get("quantite"),
                    "price": item.get("price"),
                    "category": item.get("category", "")
                })

            parsed_data = {
                "merchant": data.get("merchant"),
                "date_time": data.get("date_time"),
                "items": mapped_items,
                "taxes": data.get("taxes"),
                "total": data.get("total"),
                "currency": data.get("currency"),
            }

            return {
                "summary": raw.get("summary"),
                "data": parsed_data,
                "raw": raw_output
            }

        except json.JSONDecodeError as e:
            logger.error(f"❌ Erreur de parsing JSON: {e}")
            raise RuntimeError("❌ La réponse GPT n'est pas un JSON valide")

        if "data" not in parsed or "summary" not in parsed:
            logger.warning("⚠️ Réponse GPT incomplète. Champs manquants : 'data' ou 'summary'")
            raise RuntimeError("❌ JSON incomplet : 'data' ou 'summary' manquant")

    except Exception as e:
        logger.error(f"❌ GPT-4 Vision : {e}")
        raise RuntimeError("Erreur GPT sur le reçu")

    finally:
        if is_pdf and os.path.exists(image_path):
            os.remove(image_path)
            logger.info("🧼 Image temporaire supprimée après traitement")


async def parse_receipt_with_xai(file_path: str, debug: bool = DEBUG_XAI_PARSER) -> dict:
    logger.info("📡 Envoi à moteur XAI (non implémenté)")
    raise NotImplementedError("🛠️ Le moteur XAI n’est pas encore disponible.")
