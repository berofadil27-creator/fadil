"""Module vidéo (cahier, section 6.4). Développé après la photo et le texte : Phase 6."""
from app.detectors.base import DetectorOutput, not_performed


def analyze(data: bytes, mime: str) -> DetectorOutput:
    return DetectorOutput(indicators=[
        not_performed("metadata", "Métadonnées", "Phase 6"),
        not_performed("keyframes", "Analyse d'images représentatives", "Phase 6"),
        not_performed("content_provenance", "Provenance (C2PA / Content Credentials)", "Phase 6"),
        not_performed("temporal_consistency", "Cohérence entre les images", "Phase 6"),
    ], limitations=["Aucun module de détection vidéo n'est encore actif : aucune conclusion n'est possible."])
