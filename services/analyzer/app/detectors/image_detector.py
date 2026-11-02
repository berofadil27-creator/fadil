"""Module photo (cahier, section 6.3). Métadonnées, provenance et modèle : Phase 4."""
from app.detectors.base import not_performed

DETECTION_AVAILABLE = False


def analyze(data: bytes, mime: str) -> list:
    return [
        not_performed("metadata", "Métadonnées", "Phase 4"),
        not_performed("content_provenance", "Provenance (C2PA / Content Credentials)", "Phase 4"),
        not_performed("visual_traces", "Traces visuelles de génération ou de modification", "Phase 4"),
    ]
