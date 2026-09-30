from fastapi import APIRouter

from app.schemas.player import ModelMetrics
from app.services import player_service

router = APIRouter(prefix="/api", tags=["model"])


@router.get("/model/metrics", response_model=ModelMetrics)
def get_model_metrics():
    return player_service.get_model_metrics()
