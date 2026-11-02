"""Module texte (cahier, section 6.2). Le modèle d'analyse sera intégré en Phase 5."""
from app.detectors.base import not_performed

DETECTION_AVAILABLE = False


def analyze(text: str) -> list:
    return [
        not_performed("linguistic_features", "Caractéristiques linguistiques", "Phase 5"),
        not_performed("repetition", "Répétitivité des formulations", "Phase 5"),
        not_performed("statistical_signals", "Indices statistiques", "Phase 5"),
    ]
