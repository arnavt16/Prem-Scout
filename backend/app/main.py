import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import model, players

app = FastAPI(title="Prem Scout API")

# Comma-separated list of allowed frontend origins, e.g.
# "http://localhost:5173,https://prem-scout.vercel.app". Defaults to local dev only.
_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173")
allowed_origins = [origin.strip() for origin in _origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(players.router)
app.include_router(model.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
