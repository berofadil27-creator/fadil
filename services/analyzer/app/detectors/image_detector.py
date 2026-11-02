"""Module photo (cahier, section 6.3).

Phase 4 (étape 1) : métadonnées + provenance C2PA. Le modèle d'analyse visuelle viendra ensuite.

Règles de conclusion (prudentes) :
- « likely_ai » seulement si le fichier DÉCLARE lui-même une création par IA
  (manifeste C2PA à signature intacte, métadonnées XMP IPTC, nom d'un outil de génération
  ou paramètres de génération dans les métadonnées) ;
- « likely_human » seulement si un manifeste C2PA d'un émetteur de confiance déclare
  une capture par appareil photo, sans aucune déclaration IA ;
- sinon « inconclusive ». Une absence d'indice n'est jamais une preuve.
"""
from app.detectors.base import DetectorOutput, not_performed
from app.schemas.analysis import Indicator
from app.services import metadata_service, provenance_service


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


def analyze(data: bytes, mime: str) -> DetectorOutput:
    meta = metadata_service.read(data)
    prov = provenance_service.check(data, mime)

    indicators = [
        _metadata_indicator(meta),
        _provenance_indicator(prov),
        not_performed("visual_traces", "Analyse visuelle par un modèle spécialisé", "Phase 4, étape 2"),
    ]

    signed = prov.status in ("valid", "trusted")
    ai_declared = (signed and bool(prov.ai_declarations)) or bool(
        meta.ai_tools or meta.generation_params or meta.xmp_ai_declared)
    capture_trusted = prov.status == "trusted" and bool(prov.capture_declarations)

    limitations = []
    if ai_declared:
        conclusion = "likely_ai"
        limitations.append("Cette conclusion repose sur ce que le fichier déclare lui-même. "
                           "Ces informations peuvent avoir été ajoutées ou modifiées.")
    elif capture_trusted:
        conclusion = "likely_human"
        limitations.append("Une capture par appareil photo est déclarée et signée, mais l'image a pu "
                           "être retouchée avant la signature.")
    else:
        conclusion = "inconclusive"
        limitations.append("Aucune déclaration exploitable n'a été trouvée dans le fichier. "
                           "L'analyse visuelle par un modèle n'est pas encore active.")
    limitations.append("Une image générée par IA peut ne contenir aucune trace dans ses métadonnées.")
    return DetectorOutput(indicators=indicators, conclusion=conclusion,
                          limitations=limitations, detection_available=True)
