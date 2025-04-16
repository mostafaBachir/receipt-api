import os
from dotenv import load_dotenv

# ============================================
# Chargement .env une seule fois (pour le dev)
# ============================================

_has_loaded = False

def load_env_once():
    global _has_loaded
    if not _has_loaded:
        if load_dotenv():
            print("✅ .env chargé avec succès")
        else:
            print("⚠️ .env non trouvé, on utilise uniquement l’environnement système")
        _has_loaded = True

# ============================================
# Accès unifié aux variables d’environnement
# ============================================

def get_env(key: str) -> str:
    load_env_once()
    
    val = os.getenv(key)
    if val and val != key:
        return val

    # fallback vers version UPPER_CASE si nom kebab-case (Azure DevOps Key Vault)
    upper_key = key.replace("-", "_").upper()
    val = os.getenv(upper_key)
    if val and val != upper_key:
        return val

    print(f"⚠️ Variable '{key}' introuvable (ni '{upper_key}')")
    return ""

# ============================================
# Options de debug
# ============================================

DEBUG_GPT_PARSER = True
DEBUG_XAI_PARSER = True


# ============================================
# 🤖 OpenAI
# ============================================

OPENAI_API_KEY = get_env("openai-api")

# ============================================
# Prompt à envoyer à l'IA
# ============================================

PROMPT = """
Tu es un assistant intelligent expert dans l’analyse de tickets de caisse écrits en français.

Ta mission : lire l’image d’un reçu et retourner **uniquement** un objet JSON contenant deux clés :
1. "data" : les données structurées extraites du reçu
2. "summary" : une phrase courte et claire résumant l’achat, en français, à destination de l’utilisateur

### 🧾 Format JSON strictement attendu :

{
  "data": {
    "merchant": "nom_du_commerce",
    "receipt_id": "ABC123456",
    "store_location": "Ville, Région",
    "date_time": "2025-04-04",
    "payment_method": "Visa",
    "items": [
      {
        "name": "nom_du_produit",
        "unit_price": 2.99,
        "quantite": 1,
        "price": 2.99,
        "category": "nom_de_categorie"
      }
    ],
    "taxes": 0.00,
    "discounts": 0.00,
    "total": 2.99,
    "currency": "CAD"
  },
  "summary": "🧾 Achat chez nom_du_commerce : 1 article pour un total de 2.99 CAD."
}

### 🎯 Contraintes obligatoires :

- Retourne **uniquement** le JSON brut, sans texte explicatif ni balises.
- Utilise **exactement** les noms de champs ci-dessus (aucune variation, abréviation ou majuscule).
- Si une donnée est absente ou incertaine, utilise :
    - `null` pour les nombres,
    - `""` pour les chaînes de caractères.
- Tous les montants doivent être en **CAD** avec deux décimales.
- Si la somme des articles ne correspond pas au `total`, ajuste intelligemment les `quantite` ou `price` pour que cela corresponde.
- Si une catégorie est incertaine, mets `"category": ""`.

Merci.
"""
