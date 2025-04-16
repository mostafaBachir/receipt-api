from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.blob import init_blob_service
from services.redis_listener import listen_to_permission_events
from core.redis import redis_client

from routes.users import router as user_router
from routes.receipts import router as receipt_router
from routes.health import router as health_router

from core.config import ALLOW_ORIGINS
# 🎯 Gestion du cycle de vie de l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_blob_service()
    try:
        import asyncio
        asyncio.create_task(listen_to_permission_events())
        print("✅ Services initialisés")
    except Exception as e:
        print(f"⚠️ Redis listener non démarré : {e}")
    yield
    await redis_client.aclose()
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
    allow_origins=ALLOW_ORIGINS,  # ⚠️ Remplacer par https://www.xpensify.ca en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],)

# ✅ Enregistrement des routes
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(user_router, prefix="/api", tags=["Users"])
app.include_router(receipt_router, prefix="/api", tags=["Receipts"])

# 🔖 Route racine (info API)
@app.get("/")
def root():
    return {"message": "Xpensify Receipt API is running 🧾"}
