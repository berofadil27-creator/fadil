"""Structure des données échangées — cahier des charges, section 7."""
from typing import Literal, Optional
from pydantic import BaseModel, Field

ContentType = Literal["text", "image", "video"]
Conclusion = Literal["likely_ai", "likely_human", "inconclusive"]
IndicatorStatus = Literal["found", "not_found", "not_performed"]
AnalysisStatus = Literal["pending", "processing", "completed", "failed"]


class TextRequest(BaseModel):
    text: str = Field(..., description="Texte à analyser")


class Indicator(BaseModel):
    name: str
    status: IndicatorStatus
    explanation: str


class AnalysisResult(BaseModel):
    analysis_id: str
    content_type: ContentType
    status: AnalysisStatus
    conclusion: Conclusion
    # Reste null tant que la signification du score n'a pas été validée par des tests.
    confidence: Optional[float] = None
    indicators: list[Indicator]
    limitations: list[str]
    created_at: str
    # false tant qu'aucun module de détection réel n'est branché pour ce type de contenu.
    detection_available: bool
    engine_version: str


class HistoryItem(BaseModel):
    analysis_id: str
    content_type: ContentType
    status: AnalysisStatus
    conclusion: Conclusion
    created_at: str


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    persistent: bool = False  # historique en mémoire jusqu'à l'arrivée de la base de données


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    phase: str
