"""Base commune des détecteurs. Règle n°1 du cahier : ne pas créer de fausses fonctionnalités.
Un indicateur non encore développé est renvoyé avec le statut « not_performed »."""
from app.schemas.analysis import Indicator


def not_performed(name: str, label: str, phase: str) -> Indicator:
    return Indicator(
        name=name,
        status="not_performed",
        explanation=f"{label} : vérification pas encore disponible (prévue en {phase}).",
    )
