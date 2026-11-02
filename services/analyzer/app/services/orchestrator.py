"""Système de tâches d'analyse (cahier, section 6.1, étapes 4 à 8).
Chaque analyse est une tâche : pending -> processing -> completed (ou failed).
Pour l'instant la tâche s'exécute pendant la requête ; la même structure permettra
plus tard un traitement en arrière-plan (vidéo, modèles lourds)."""
import uuid
from datetime import datetime, timezone
from typing import Callable
from app.core import config
from app.schemas.analysis import AnalysisResult, ContentType
from app.services import store
from app.detectors.base import DetectorOutput

BASE_LIMITATIONS = [
    "VEYRA ne permet jamais de déterminer avec certitude l'origine d'un contenu.",
]


def run(client_id: str, content_type: ContentType, detector: Callable[[], DetectorOutput]) -> AnalysisResult:
    result = AnalysisResult(
        analysis_id=str(uuid.uuid4()),
        content_type=content_type,
        status="pending",
        conclusion="inconclusive",
        confidence=None,
        indicators=[],
        limitations=[],
        created_at=datetime.now(timezone.utc).isoformat(),
        detection_available=False,
        engine_version=f"{config.VERSION}-{config.PHASE}",
    )
    store.save(client_id, result)
    result.status = "processing"
    try:
        out = detector()
        result.indicators = out.indicators
        result.detection_available = out.detection_available
        # Sans aucun indice réellement vérifié, la conclusion reste indéterminée.
        verified = any(i.status != "not_performed" for i in out.indicators)
        result.conclusion = out.conclusion if verified else "inconclusive"
        result.limitations = list(out.limitations) + BASE_LIMITATIONS
        result.status = "completed"
    except Exception:
        result.status = "failed"
        result.limitations = ["L'analyse a échoué. Aucun résultat n'a été produit."]
    store.save(client_id, result)
    return result
