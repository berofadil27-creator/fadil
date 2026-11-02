"""VEYRA — moteur d'analyse (FastAPI). Documentation interactive : /docs"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core import config
from app.core.errors import register_error_handlers
from app.routes import analysis, analyze, health

app = FastAPI(
    title=config.APP_NAME,
    version=config.VERSION,
    description="API de VEYRA. Phase 3 : serveur, routes, validation, erreurs et tâches. "
                "Aucun module de détection n'est encore actif.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-Client-Id"],
)
register_error_handlers(app)
app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(analysis.router)
