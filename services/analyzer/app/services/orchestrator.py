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

BASE_LIMITATIONS = [
    "VEYRA ne permet jamais de déterminer avec certitude l'origine d'un contenu.",
]


def run(client_id: str, content_type: ContentType, detector: Callable[[], list],
        detection_available: bool) -> AnalysisResult:
    result = AnalysisResult(
        analysis_id=str(uuid.uuid4()),
        content_type=content_type,
        status="pending",
        conclusion="inconclusive",
        confidence=None,
        indicators=[],
        limitations=[],
        created_at=datetime.now(timezone.utc).isoformat(),
        detection_available=detection_available,
        engine_version=f"{config.VERSION}-{config.PHASE}",
    )
    store.save(client_id, result)
    result.status = "processing"
    try:
        result.indicators = detector()
        result.conclusion = conclude(result.indicators)
        result.limitations = list(BASE_LIMITATIONS)
        if not detection_available:
            result.limitations.insert(0,
                "Le serveur a bien reçu et vérifié votre contenu, mais aucun module de "
                "détection n'est encore actif : aucune conclusion n'est possible.")
        result.status = "completed"
    except Exception:
        result.status = "failed"
        result.limitations = ["L'analyse a échoué. Aucun résultat n'a été produit."]
    store.save(client_id, result)
    return result


def conclude(indicators: list) -> str:
    """Conclusion prudente : sans indice réellement vérifié, le résultat reste indéterminé."""
    if not any(i.status != "not_performed" for i in indicators):
        return "inconclusive"
    # Les règles de décision seront définies et testées avec les premiers modules réels.
    return "inconclusive"
