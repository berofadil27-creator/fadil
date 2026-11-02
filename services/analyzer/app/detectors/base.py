"""Base commune des détecteurs. Règle n°1 du cahier : ne pas créer de fausses fonctionnalités.
Un indicateur non encore développé est renvoyé avec le statut « not_performed »."""
from dataclasses import dataclass, field
from app.schemas.analysis import Indicator


@dataclass
class DetectorOutput:
    indicators: list
    conclusion: str = "inconclusive"
    limitations: list = field(default_factory=list)
    detection_available: bool = False


def not_performed(name: str, label: str, phase: str) -> Indicator:
    return Indicator(
        name=name,
        status="not_performed",
        explanation=f"{label} : vérification pas encore disponible (prévue en {phase}).",
    )
