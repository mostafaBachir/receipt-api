from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from routes.receipts import router as receipt_router
from routes.health import router as health_router

# 🎯 Gestion du cycle de vie de l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        print("✅ Services initialisés")
    except Exception as e:
        print(f"⚠️ Services initialization error: {e}")
    yield
    print("🛑 Xpensify Receipt API arrêtée proprement.")

# 🚀 Création de l'application
app = FastAPI(
    title="Xpensify Receipt API",
    description="API de gestion des reçus avec parsing IA",
    version="1.0.0",
    lifespan=lifespan
)

# 🌍 Middleware CORS pour autoriser le front local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Enregistrement des routes
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(receipt_router, prefix="/api", tags=["Receipts"])

# 🔖 Route racine (info API)
@app.get("/")
def root():
    return {"message": "Xpensify Receipt API is running 🧾"}
