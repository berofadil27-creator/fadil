"""Module vidéo (cahier, section 6.4). Phase 6.1.

Pour respecter la limite d'envoi de Vercel (~4,5 Mo) et ne jamais stocker la vidéo, le navigateur
extrait quelques images à intervalles réguliers et n'envoie QUE ces images. Chaque image est
analysée par le modèle visuel (Sightengine « genai »), puis les résultats sont comparés.

Règles de conclusion (prudentes, seuils provisoires) :
- moins de 3 images analysées : « inconclusive » ;
- au moins 2/3 des images analysées avec des traces IA nettes : « likely_ai » ;
- toutes les images analysées (au moins 4) sans trace IA : « likely_human », avec la limite que
  le modèle ne repère pas les échanges de visage, les retouches partielles ni le son ;
- sinon « inconclusive ».
Le rapport dit toujours combien d'images ont été examinées : jamais « toute la vidéo ».
"""
import math
from concurrent.futures import ThreadPoolExecutor

from app.detectors.base import DetectorOutput
from app.schemas.analysis import Indicator
from app.services import visual_model_service as vms


def _fmt_time(t: float) -> str:
    t = max(0, int(round(t)))
    return f"{t // 60}:{t % 60:02d}"


def analyze(frames: list[bytes], timestamps: list[float], duration: float | None) -> DetectorOutput:
    n = len(frames)
    not_sent = Indicator(name="content_provenance", status="not_performed", explanation=(
        "Métadonnées et provenance C2PA non vérifiées : seule une sélection d'images est envoyée au "
        "serveur, pas le fichier vidéo lui-même."))
    if not vms.configured():
        kf = Indicator(name="keyframes", status="not_performed",
                       explanation="Analyse des images non disponible : le modèle visuel n'est pas configuré.")
        return DetectorOutput(indicators=[kf, not_sent], limitations=[
            "Aucune analyse vidéo n'a pu être effectuée : aucune conclusion n'est possible."])
    if not vms.take_quota(n):
        kf = Indicator(name="keyframes", status="not_performed", explanation=(
            "Analyse des images non effectuée : le quota quotidien du prototype est atteint. Réessayez demain."))
        return DetectorOutput(indicators=[kf, not_sent], limitations=[
            "Aucune analyse vidéo n'a pu être effectuée : aucune conclusion n'est possible."])

    with ThreadPoolExecutor(max_workers=min(n, 6)) as pool:
        reports = list(pool.map(lambda f: vms.analyze(f, "frame.jpg", reserved=True), frames))
    ok = [(t, r) for t, r in zip(timestamps, reports) if r.status == "ok"]
    high = [t for t, r in ok if r.level == "high"]
    low = [t for t, r in ok if r.level == "low"]
    unc = [t for t, r in ok if r.level == "uncertain"]
    k = len(ok)

    span = f" d'une vidéo de {_fmt_time(duration)}" if duration else ""
    if k == 0:
        keyframes = Indicator(name="keyframes", status="not_performed", explanation=(
            f"{n} images ont été extraites{span}, mais le service d'analyse n'a pas répondu. Réessayez plus tard."))
    else:
        parts = []
        if high:
            parts.append(f"{len(high)} avec de nombreuses caractéristiques typiques de l'IA "
                         f"(à {', '.join(_fmt_time(t) for t in high)})")
        if unc:
            parts.append(f"{len(unc)} ambiguë{'s' if len(unc) > 1 else ''}")
        if low:
            parts.append(f"{len(low)} sans caractéristique typique de l'IA")
        status = "found" if high else ("not_found" if len(low) == k else "uncertain")
        keyframes = Indicator(name="keyframes", status=status, explanation=(
            f"{k} images réparties régulièrement{span} ont été analysées par le modèle visuel "
            f"(Sightengine) : " + ", ".join(parts) + ". Le reste de la vidéo n'a pas été examiné."))

    if k < 2:
        temporal = Indicator(name="temporal_consistency", status="not_performed",
                             explanation="Pas assez d'images analysées pour les comparer entre elles.")
    elif high and low:
        temporal = Indicator(name="temporal_consistency", status="found", explanation=(
            "Les images donnent des résultats divergents : la vidéo pourrait mêler des passages réels et "
            "artificiels, ou le modèle est hésitant sur certaines scènes. Seuls les résultats par image "
            "sont comparés, pas le mouvement."))
    else:
        temporal = Indicator(name="temporal_consistency", status="not_found", explanation=(
            "Les images analysées donnent des résultats cohérents entre elles. Seuls les résultats par "
            "image sont comparés, pas le mouvement."))

    limitations = []
    if k < 3:
        conclusion = "inconclusive"
        limitations.append("Trop peu d'images ont pu être analysées pour conclure.")
    elif len(high) >= math.ceil(2 * k / 3):
        conclusion = "likely_ai"
        limitations.append("Cette conclusion repose sur un modèle statistique appliqué à quelques images : "
                           "une vraie vidéo très retouchée ou compressée peut être classée à tort.")
    elif len(low) == k and k >= 4:
        conclusion = "likely_human"
        limitations.append("Le modèle ne repère pas les échanges de visage (deepfakes), les retouches "
                           "partielles ni les voix générées : une vidéo réelle modifiée peut passer inaperçue.")
    else:
        conclusion = "inconclusive"
        limitations.append("Les images analysées ne permettent pas de conclure.")
    limitations += [f"Seules {k} images sur l'ensemble de la vidéo ont été examinées." if k else
                    "Aucune image n'a pu être examinée.",
                    "Le son n'est pas analysé.",
                    "Aucun score n'est affiché : sa signification n'a pas encore été validée par nos propres tests."]
    return DetectorOutput(indicators=[keyframes, temporal, not_sent], conclusion=conclusion,
                          limitations=limitations, detection_available=k > 0)
