"""Module photo (cahier, section 6.3).

Phase 4 : métadonnées + provenance C2PA + analyse visuelle par un modèle spécialisé.

Règles de conclusion (prudentes) :
- « likely_ai » si le fichier DÉCLARE une création par IA (C2PA intact, XMP IPTC, outil ou
  paramètres de génération), ou si le modèle visuel détecte un niveau élevé de traces IA
  sans déclaration contraire de confiance ;
- « likely_human » si un manifeste C2PA de confiance déclare une capture, ou si le modèle
  visuel ne détecte quasiment aucune trace IA, et qu'aucun autre indice ne dit le contraire ;
- sinon « inconclusive ». Une absence d'indice n'est jamais une preuve.
"""
from app.detectors.base import DetectorOutput, not_performed
from app.schemas.analysis import Indicator
from app.services import metadata_service, provenance_service, visual_model_service


def _metadata_indicator(meta: metadata_service.MetadataReport) -> Indicator:
    if not meta.readable:
        return Indicator(name="metadata", status="not_found",
                         explanation="Le fichier n'a pas pu être décodé comme image : métadonnées illisibles.")
    if not meta.has_any:
        return Indicator(name="metadata", status="not_found", explanation=(
            "Aucune métadonnée utile (appareil, logiciel, date). C'est fréquent : les réseaux sociaux et "
            "les captures d'écran les suppriment. Cela ne dit rien de l'origine de l'image."))
    parts = []
    if meta.ai_tools:
        parts.append("outil de génération mentionné : " + ", ".join(meta.ai_tools))
    if meta.generation_params:
        parts.append("paramètres de génération d'image (typiques de Stable Diffusion / ComfyUI) présents")
    if meta.xmp_ai_declared:
        parts.append("le champ IPTC « type de source » déclare un contenu créé par IA")
    if meta.camera:
        parts.append(f"appareil indiqué : {meta.camera}")
    if meta.software:
        parts.append(f"logiciel indiqué : {meta.software}")
    if meta.date_taken:
        parts.append(f"date de prise de vue indiquée : {meta.date_taken}")
    return Indicator(name="metadata", status="found", explanation=(
        "Métadonnées trouvées — " + " ; ".join(parts) + ". Les métadonnées peuvent être modifiées : "
        "ce sont des indices, pas des preuves."))


def _provenance_indicator(prov: provenance_service.ProvenanceReport) -> Indicator:
    if prov.status == "absent":
        return Indicator(name="content_provenance", status="not_found", explanation=(
            "Aucune information de provenance C2PA (Content Credentials). La plupart des images n'en ont "
            "pas : leur absence ne signifie pas que le contenu est artificiel."))
    if prov.status == "remote_not_checked":
        return Indicator(name="content_provenance", status="found", explanation=(
            "Le fichier renvoie vers des informations de provenance stockées en ligne. Par sécurité, "
            "VEYRA ne les a pas téléchargées : elles n'ont pas été vérifiées."))
    if prov.status == "error":
        return Indicator(name="content_provenance", status="not_performed", explanation=(
            "La vérification de provenance n'a pas pu être effectuée sur ce fichier."))
    if prov.status == "invalid":
        return Indicator(name="content_provenance", status="found", explanation=(
            "Des informations de provenance C2PA sont présentes, mais leur vérification échoue : le fichier "
            "a probablement été modifié après la signature. Elles ne peuvent pas être prises en compte."))
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
        f"Informations de provenance C2PA intactes, {who} ({trust}){extra}."))


def _visual_indicator(vis: visual_model_service.VisualReport) -> Indicator:
    if vis.status == "unconfigured":
        return not_performed("visual_traces", "Analyse visuelle par un modèle spécialisé", "Phase 4")
    if vis.status in ("quota", "error"):
        reason = ("le quota quotidien du prototype est atteint" if vis.status == "quota"
                  else "le service d'analyse n'a pas répondu")
        return Indicator(name="visual_traces", status="not_performed",
                         explanation=f"Analyse visuelle non effectuée : {reason}. Réessayez plus tard.")
    texts = {
        "high": "Le modèle d'analyse visuelle relève de nombreuses caractéristiques typiques des images "
                "générées ou retouchées par IA.",
        "low": "Le modèle d'analyse visuelle ne relève quasiment aucune caractéristique typique des images IA.",
        "uncertain": "Le modèle d'analyse visuelle ne permet pas de trancher : les caractéristiques observées "
                     "sont ambiguës.",
    }
    status = "found" if vis.level == "high" else "not_found" if vis.level == "low" else "uncertain"
    return Indicator(name="visual_traces", status=status, explanation=texts[vis.level] + (
        " Ce modèle (Sightengine) analyse uniquement les pixels ; il peut se tromper, notamment sur "
        "les images très compressées, les captures d'écran ou les générateurs récents."))


def analyze(data: bytes, mime: str) -> DetectorOutput:
    meta = metadata_service.read(data)
    prov = provenance_service.check(data, mime)
    vis = visual_model_service.analyze(data)

    indicators = [_metadata_indicator(meta), _provenance_indicator(prov), _visual_indicator(vis)]

    signed = prov.status in ("valid", "trusted")
    ai_declared = (signed and bool(prov.ai_declarations)) or bool(
        meta.ai_tools or meta.generation_params or meta.xmp_ai_declared)
    capture_trusted = prov.status == "trusted" and bool(prov.capture_declarations)
    model_high = vis.status == "ok" and vis.level == "high"
    model_low = vis.status == "ok" and vis.level == "low"

    limitations = []
    if ai_declared:
        conclusion = "likely_ai"
        limitations.append("Le fichier déclare lui-même une création par IA. Ces informations peuvent "
                           "avoir été ajoutées ou modifiées.")
        if model_low:
            limitations.append("Le modèle visuel, lui, ne relève pas de traces IA : les indices divergent.")
    elif capture_trusted and model_high:
        conclusion = "inconclusive"
        limitations.append("Les indices se contredisent : une capture par appareil photo est déclarée et "
                           "signée, mais le modèle visuel relève des traces typiques de l'IA.")
    elif capture_trusted:
        conclusion = "likely_human"
        limitations.append("Une capture par appareil photo est déclarée et signée par un émetteur de "
                           "confiance, mais l'image a pu être retouchée avant la signature.")
    elif model_high:
        conclusion = "likely_ai"
        limitations.append("Cette conclusion repose sur un modèle statistique : une vraie photo peut être "
                           "classée à tort, en particulier si elle a été fortement retouchée.")
    elif model_low:
        conclusion = "likely_human"
        limitations.append("Cette conclusion repose sur un modèle statistique : une image IA récente ou "
                           "retravaillée peut ne pas être détectée.")
    else:
        conclusion = "inconclusive"
        limitations.append("Les éléments disponibles ne permettent pas de conclure.")
    if vis.status == "ok":
        limitations.append("Aucun score n'est affiché : sa signification n'a pas encore été validée par "
                           "nos propres tests.")
    return DetectorOutput(indicators=indicators, conclusion=conclusion,
                          limitations=limitations, detection_available=True)
