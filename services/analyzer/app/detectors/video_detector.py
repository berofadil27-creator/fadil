"""Module vidéo (cahier, section 6.4). Développé après la photo et le texte : Phase 6."""
from app.detectors.base import not_performed

DETECTION_AVAILABLE = False


def analyze(data: bytes, mime: str) -> list:
    return [
        not_performed("metadata", "Métadonnées", "Phase 6"),
        not_performed("keyframes", "Analyse d'images représentatives", "Phase 6"),
        not_performed("content_provenance", "Provenance (C2PA / Content Credentials)", "Phase 6"),
        not_performed("temporal_consistency", "Cohérence entre les images", "Phase 6"),
    ]
