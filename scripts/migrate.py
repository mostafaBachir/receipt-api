import sys
from pymongo import MongoClient
from datetime import datetime

# Connexion MongoDB
client = MongoClient("mongodb+srv://xpadmin:SuperSecure123!@xpensify-mongo.global.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000")

db = client["xpensify"]
expenses_collection = db["Expense"]
migration_collection = db["migration_versions"]

# --flush option
def flush_db():
    print("💣 Suppression de tous les reçus et des versions de migration...")
    expenses_collection.delete_many({})
    migration_collection.delete_many({})
    print("✅ Base vidée avec succès.\n")

# --- MIGRATIONS VERSIONNÉES ---

def migration_001_prepare_items_for_total_front_validation():
    print("🔧 [001] Vérifie que chaque item a un champ 'price' (None si absent)")

    receipts = expenses_collection.find({})
    for receipt in receipts:
        updated_items = []
        modified = False

        for item in receipt.get("items", []):
            if "price" not in item:
                item["price"] = None
                modified = True
            updated_items.append(item)

        if modified:
            expenses_collection.update_one(
                {"_id": receipt["_id"]},
                {"$set": {"items": updated_items}}
            )
            print(f"   ↪️ Reçu mis à jour : {receipt.get('_id')}")

migrations = [
    ("001_prepare_items_for_total_front_validation", migration_001_prepare_items_for_total_front_validation),
]

def already_applied(version_id):
    return migration_collection.find_one({"version": version_id}) is not None

def mark_as_applied(version_id):
    migration_collection.insert_one({
        "version": version_id,
        "applied_at": datetime.utcnow()
    })

def run_migrations():
    for version_id, migration_func in migrations:
        if already_applied(version_id):
            print(f"✅ {version_id} déjà appliquée")
        else:
            print(f"🚀 Application de {version_id}")
            try:
                migration_func()
                mark_as_applied(version_id)
                print(f"✅ {version_id} appliquée avec succès\n")
            except Exception as e:
                print(f"❌ Erreur sur {version_id}: {e}")
                break

# --- CRÉATION DES INDEXS ---

def create_receipt_indexes():
    print("🔧 Création des index MongoDB...")

    expenses_collection.create_index(
        [("user_id", 1), ("original_signature", 1)],
        name="user_original_signature_index"
    )

    expenses_collection.create_index(
        [("user_id", 1), ("optimized_signature", 1)],
        name="user_optimized_signature_index"
    )

    expenses_collection.create_index(
        [("user_id", 1), ("original_signature", 1)],
        name="unique_user_original_signature",
        unique=True,
        sparse=True
    )

    print("✅ Index créés avec succès.\n")

# --- MAIN ---

if __name__ == "__main__":
    if "--flush" in sys.argv:
        flush_db()

    run_migrations()
    create_receipt_indexes()
