from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator, model_validator

# 🛒 Représente un produit sur le reçu
class Item(BaseModel):
    name: str
    unit_price: float
    quantite: Optional[float] = 1.0
    price: Optional[float] = None
    category: Optional[str] = None

    @field_validator("price", mode="before")
    @classmethod
    def log_missing_price(cls, v):
        if v is None:
            print("⚠️  price est manquant, à valider manuellement")
        return v

# 🧾 Modèle principal d’un reçu
class ReceiptModel(BaseModel):
    id: Optional[str] = None
    receipt_id: Optional[str] = None
    user_id: str
    filename: str
    blob_url: str
    summary: str
    merchant: str
    store_location: Optional[str] = None
    date_time: Optional[datetime] = None
    subtotal: Optional[float] = None
    taxes: Optional[float] = 0.0
    discounts: Optional[float] = 0.0
    total: float
    currency: str = "CAD"
    payment_method: Optional[str] = None
    note: Optional[str] = None
    manual_entry: bool = False
    is_split: bool = False
    items_count: int
    tags: Optional[List[str]] = []
    original_signature: Optional[str] = None
    optimized_signature: Optional[str] = None
    parser: Optional[str] = "human"
    reviewed_and_corrected: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    items: List[Item]

    @model_validator(mode="after")
    @classmethod
    def log_items_to_review(cls, values):
        items: List[Item] = values.get("items", [])
        incomplets = [item for item in items if item.price is None]

        if incomplets:
            print(f"\n🔍 Reçu à corriger : {len(incomplets)} article(s) sans prix total (`price = None`)")
            for item in incomplets:
                print(f"   → {item.name} (unit_price = {item.unit_price}, quantité = {item.quantite})")
        return values

class ReceiptUpdateModel(BaseModel):
    """
    Modèle utilisé pour la mise à jour d'un reçu.
    Tous les champs sont facultatifs, sauf `user_id` qui est vérifié si présent.
    """
    merchant: Optional[str] = None
    date_time: Optional[datetime] = None
    total: Optional[float] = None
    items: Optional[List[Item]] = None
    user_id: Optional[str] = None
    reviewed_and_corrected: Optional[bool] = True