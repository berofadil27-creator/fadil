"""Module texte (cahier, section 6.2). Le modèle d'analyse sera intégré en Phase 5."""
from app.detectors.base import DetectorOutput, not_performed


def analyze(text: str) -> DetectorOutput:
    return DetectorOutput(indicators=[
        not_performed("linguistic_features", "Caractéristiques linguistiques", "Phase 5"),
        not_performed("repetition", "Répétitivité des formulations", "Phase 5"),
        not_performed("statistical_signals", "Indices statistiques", "Phase 5"),
    ], limitations=["Aucun module de détection de texte n'est encore actif : aucune conclusion n'est possible."])
