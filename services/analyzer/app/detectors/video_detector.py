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
import json
import math
from concurrent.futures import ThreadPoolExecutor

from app.detectors.base import DetectorOutput
from app.schemas.analysis import Indicator
from app.services import visual_model_service as vms
from app.services.provenance_service import AI_SOURCE_TYPES, CAPTURE_SOURCE_TYPES, ProvenanceReport

_CLIENT_STATUSES = {"absent", "invalid", "valid", "trusted", "error"}


def parse_client_provenance(raw: str | None) -> ProvenanceReport | None:
    """Résumé C2PA lu par le navigateur (étape 8.5). Non vérifiable par le serveur : il est
    validé strictement, et tout ce qui est mal formé est ignoré."""
    if not raw or len(raw) > 4000:
        return None
    try:
        d = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(d, dict) or d.get("status") not in _CLIENT_STATUSES:
        return None

    def _s(v):
        return v.strip()[:200] or None if isinstance(v, str) else None

    types = [t for t in d.get("source_types") or [] if isinstance(t, str)][:10]
    return ProvenanceReport(
        status=d["status"], issuer=_s(d.get("issuer")), generator=_s(d.get("generator")),
        ai_declarations=sorted({AI_SOURCE_TYPES[t] for t in types if t in AI_SOURCE_TYPES}),
        capture_declarations=sorted({CAPTURE_SOURCE_TYPES[t] for t in types if t in CAPTURE_SOURCE_TYPES}),
    )


_BY_DEVICE = " Lu par votre appareil : la vidéo n'est pas envoyée, le serveur ne peut donc pas le revérifier."


def _provenance_indicator(prov: ProvenanceReport | None) -> Indicator:
    if prov is None:
        return Indicator(name="content_provenance", status="not_performed", explanation=(
            "Métadonnées et provenance C2PA non vérifiées : seule une sélection d'images est envoyée au "
            "serveur, pas le fichier vidéo lui-même."))
    if prov.status == "absent":
        return Indicator(name="content_provenance", status="not_found", explanation=(
            "Aucune information de provenance C2PA (Content Credentials) dans le fichier. La plupart des "
            "vidéos n'en ont pas, et les réseaux sociaux les retirent souvent : leur absence ne signifie "
            "pas que la vidéo est artificielle." + _BY_DEVICE))
    if prov.status == "error":
        return Indicator(name="content_provenance", status="not_performed", explanation=(
            "La provenance C2PA n'a pas pu être lue sur cet appareil (format non pris en charge, "
            "fichier trop lourd ou délai dépassé)."))
    if prov.status == "invalid":
        return Indicator(name="content_provenance", status="found", explanation=(
            "Des informations de provenance C2PA sont présentes, mais leur vérification échoue : le fichier "
            "a probablement été modifié après la signature. Elles ne peuvent pas être prises en compte."
            + _BY_DEVICE))
    who = f"signées par « {prov.issuer} »" if prov.issuer else "signées"
    trust = ("émetteur reconnu par une liste de confiance" if prov.status == "trusted"
             else "émetteur non vérifié auprès d'une liste de confiance")
    decl = []
    if prov.ai_declarations:
        decl.append("contenu déclaré " + " et ".join(prov.ai_declarations))
    if prov.capture_declarations:
        decl.append("contenu déclaré " + " et ".join(prov.capture_declarations))
    if prov.generator:
        decl.append(f"outil de création : {prov.generator}")
    extra = (" — " + " ; ".join(decl)) if decl else ""
    return Indicator(name="content_provenance", status="found", explanation=(
        f"Informations de provenance C2PA intactes, {who} ({trust}){extra}." + _BY_DEVICE))


def _fmt_time(t: float) -> str:
    t = max(0, int(round(t)))
    return f"{t // 60}:{t % 60:02d}"


def _no_frames(kf: Indicator, prov_ind: Indicator, ai_declared: bool) -> DetectorOutput:
    if ai_declared:
        return DetectorOutput(indicators=[kf, prov_ind], conclusion="likely_ai", detection_available=True,
                              limitations=["Seule la déclaration C2PA du fichier (lue par votre appareil) a été "
                                           "prise en compte : les images n'ont pas été analysées. Ces informations "
                                           "peuvent avoir été ajoutées ou modifiées."])
    return DetectorOutput(indicators=[kf, prov_ind], limitations=[
        "Aucune analyse vidéo n'a pu être effectuée : aucune conclusion n'est possible."])


def analyze(frames: list[bytes], timestamps: list[float], duration: float | None,
            provenance: ProvenanceReport | None = None) -> DetectorOutput:
    n = len(frames)
    not_sent = _provenance_indicator(provenance)
    ai_declared = bool(provenance and provenance.status in ("valid", "trusted") and provenance.ai_declarations)
    if not vms.configured():
        kf = Indicator(name="keyframes", status="not_performed",
                       explanation="Analyse des images non disponible : le modèle visuel n'est pas configuré.")
        return _no_frames(kf, not_sent, ai_declared)
    if not vms.take_quota(n):
        kf = Indicator(name="keyframes", status="not_performed", explanation=(
            "Analyse des images non effectuée : le quota quotidien du prototype est atteint. Réessayez demain."))
        return _no_frames(kf, not_sent, ai_declared)

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
    hint = None
    if ai_declared:
        conclusion = "likely_ai"
        limitations.append("Le fichier vidéo déclare lui-même une création par IA (C2PA, lu par votre appareil). "
                           "Ces informations peuvent avoir été ajoutées ou modifiées.")
        if k >= 3 and len(low) == k:
            limitations.append("Le modèle visuel, lui, ne relève pas de traces IA : les indices divergent.")
    elif k < 3:
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
    elif len(high) * 2 >= k:
        # Étape 8.6 : au moins la moitié des images ont des traces IA nettes, sans atteindre 2/3.
        # Indice d'IA affiché, mais pas de conclusion ferme : une vraie vidéo peut être concernée.
        conclusion = "inconclusive"
        hint = Indicator(name="ai_hint", status="found", explanation=(
            f"Indice d'IA : {len(high)} images sur {k} présentent de nombreuses caractéristiques typiques "
            "de l'IA. C'est un signal, pas une preuve : il n'atteint pas le seuil de conclusion (2/3 des images)."))
        limitations.append("La moitié au moins des images analysées évoquent une génération IA, mais pas assez "
                           "pour conclure : une vraie vidéo retouchée ou compressée peut produire ce résultat.")
    else:
        conclusion = "inconclusive"
        limitations.append("Les images analysées ne permettent pas de conclure.")
    limitations += [f"Seules {k} images sur l'ensemble de la vidéo ont été examinées." if k else
                    "Aucune image n'a pu être examinée.",
                    "Le son n'est pas analysé.",
                    "Aucun score n'est affiché : sa signification n'a pas encore été validée par nos propres tests."]
    indicators = [keyframes, temporal, not_sent] + ([hint] if hint else [])
    return DetectorOutput(indicators=indicators, conclusion=conclusion,
                          limitations=limitations, detection_available=k > 0 or ai_declared)
