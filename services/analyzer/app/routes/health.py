from fastapi import APIRouter
from app.core import config
from app.schemas.analysis import HealthResponse

router = APIRouter()


@router.get("/api/health", response_model=HealthResponse, summary="Vérifier que le serveur fonctionne")
def health():
    return HealthResponse(status="ok", service=config.APP_NAME, version=config.VERSION, phase=config.PHASE)
