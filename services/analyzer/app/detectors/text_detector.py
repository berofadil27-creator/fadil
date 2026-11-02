"""Module texte (cahier, section 6.2). Phase 5 : modèle open source expérimental.

Règles de conclusion (prudentes) :
- « likely_ai » seulement si le modèle relève des traces IA nettes ;
- jamais « likely_human » : le modèle laisse passer une partie des textes IA, donc un score bas
  n'est pas une preuve d'écriture humaine ;
- sinon « inconclusive ».
"""
from app.detectors.base import DetectorOutput, not_performed
from app.schemas.analysis import Indicator
from app.services import text_model_service

CAVEAT = (" Ce modèle expérimental (CamemBERTa, entraîné sur des textes ChatGPT de 2023) n'est fiable "
          "qu'en français et peut se tromper, surtout sur les textes courts, retravaillés ou produits par "
          "des IA récentes.")


def _model_indicator(rep: text_model_service.TextModelReport) -> Indicator:
    if rep.status == "unconfigured":
        return not_performed("statistical_signals", "Analyse statistique par un modèle", "Phase 5")
    if rep.status == "error":
        return Indicator(name="statistical_signals", status="not_performed", explanation=(
            "Analyse par le modèle non effectuée : le service n'a pas répondu (il peut être en veille "
            "et mettre une minute à redémarrer). Réessayez plus tard."))
    texts = {
        "high": "Le modèle relève de nombreuses tournures typiques des textes générés par IA.",
        "low": "Le modèle relève peu de tournures typiques de l'IA. Cela ne prouve pas que le texte "
               "a été écrit par un humain.",
        "uncertain": "Le modèle ne permet pas de trancher : les indices sont ambigus.",
    }
    status = {"high": "found", "low": "not_found", "uncertain": "uncertain"}[rep.level]
    return Indicator(name="statistical_signals", status=status, explanation=texts[rep.level] + CAVEAT)


def analyze(text: str) -> DetectorOutput:
    rep = text_model_service.analyze(text)
    indicators = [
        _model_indicator(rep),
        not_performed("linguistic_features", "Caractéristiques linguistiques détaillées", "une phase ultérieure"),
        not_performed("repetition", "Répétitivité des formulations", "une phase ultérieure"),
    ]
    if rep.status != "ok":
        return DetectorOutput(indicators=indicators, limitations=[
            "Aucune analyse de texte n'a pu être effectuée : aucune conclusion n'est possible."])
    limitations = ["Module texte expérimental, validé seulement sur un petit jeu de textes français.",
                   "Aucun score n'est affiché : sa signification n'a pas encore été validée par des tests plus larges."]
    if rep.level == "high":
        conclusion = "likely_ai"
        limitations.insert(0, "Un texte humain très formel ou stéréotypé peut être classé à tort.")
    else:
        conclusion = "inconclusive"
        limitations.insert(0, "Un texte IA peut passer inaperçu : l'absence d'indices n'est pas une preuve.")
    return DetectorOutput(indicators=indicators, conclusion=conclusion,
                          limitations=limitations, detection_available=True)
