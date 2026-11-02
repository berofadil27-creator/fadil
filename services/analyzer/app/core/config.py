"""Configuration commune du moteur d'analyse VEYRA.

Les limites ci-dessous sont des choix provisoires (non fixés par le cahier des charges)
et identiques à celles du site. Elles peuvent être modifiées par variables d'environnement.
"""
import os

def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default

APP_NAME = "VEYRA Analyzer"
VERSION = "0.1.0"
PHASE = "phase-3"

TEXT_MIN_CHARS = _int("VEYRA_TEXT_MIN_CHARS", 300)
TEXT_MAX_CHARS = _int("VEYRA_TEXT_MAX_CHARS", 20_000)
IMAGE_MAX_BYTES = _int("VEYRA_IMAGE_MAX_BYTES", 10 * 1024 * 1024)
VIDEO_MAX_BYTES = _int("VEYRA_VIDEO_MAX_BYTES", 100 * 1024 * 1024)

IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm"}

# Limite d'utilisation simple, par client anonyme (en attendant les comptes Supabase).
RATE_LIMIT_PER_HOUR = _int("VEYRA_RATE_LIMIT_PER_HOUR", 30)

# Origines autorisées à appeler l'API depuis un navigateur (séparées par des virgules).
CORS_ORIGINS = [o.strip() for o in os.getenv(
    "VEYRA_CORS_ORIGINS",
    "http://localhost:3000,https://veyra-theta-sable.vercel.app",
).split(",") if o.strip()]
