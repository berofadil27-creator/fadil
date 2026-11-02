"""Analyse visuelle par un modèle spécialisé : Sightengine, modèle « genai ».

Le modèle analyse uniquement les pixels (pas les métadonnées). Il renvoie un score de 0 à 1.
Règle du cahier (section 7) : ce score n'est PAS affiché comme une probabilité tant que sa
signification n'a pas été validée par nos propres tests. Il est traduit en niveaux prudents.
Seuils provisoires, à évaluer en Phase 4 sur des jeux de photos représentatifs.
"""
import os
import time
from dataclasses import dataclass
from threading import Lock

import httpx

API_URL = "https://api.sightengine.com/1.0/check.json"
HIGH = float(os.getenv("VEYRA_GENAI_HIGH", "0.90"))
LOW = float(os.getenv("VEYRA_GENAI_LOW", "0.10"))
# Offre gratuite Sightengine : 500 opérations/jour, 5 opérations par image => 100 images/jour.
DAILY_CAP = int(os.getenv("VEYRA_GENAI_DAILY_CAP", "90"))

_lock = Lock()
_day = {"date": "", "count": 0}


@dataclass
class VisualReport:
    status: str  # "ok" | "unconfigured" | "quota" | "error"
    level: str | None = None  # "high" | "low" | "uncertain"
    score: float | None = None  # gardé côté serveur, jamais affiché tel quel


def configured() -> bool:
    return bool(os.getenv("SIGHTENGINE_API_USER") and os.getenv("SIGHTENGINE_API_SECRET"))


def take_quota(n: int = 1) -> bool:
    """Réserve n images sur le plafond quotidien (tout ou rien)."""
    today = time.strftime("%Y-%m-%d", time.gmtime())
    with _lock:
        if _day["date"] != today:
            _day.update(date=today, count=0)
        if _day["count"] + n > DAILY_CAP:
            return False
        _day["count"] += n
        return True


def analyze(data: bytes, filename: str = "image", reserved: bool = False) -> VisualReport:
    user, secret = os.getenv("SIGHTENGINE_API_USER"), os.getenv("SIGHTENGINE_API_SECRET")
    if not user or not secret:
        return VisualReport(status="unconfigured")
    if not reserved and not take_quota():
        return VisualReport(status="quota")
    try:
        r = httpx.post(API_URL, timeout=20.0,
                       data={"models": "genai", "api_user": user, "api_secret": secret},
                       files={"media": (filename, data)})
        body = r.json()
        if r.status_code != 200 or body.get("status") != "success":
            return VisualReport(status="error")
        score = float(body["type"]["ai_generated"])
    except Exception:  # noqa: BLE001
        return VisualReport(status="error")
    level = "high" if score >= HIGH else "low" if score <= LOW else "uncertain"
    return VisualReport(status="ok", level=level, score=score)
