"""Module de provenance (cahier, section 6.5) — C2PA / Content Credentials.

Ce que ce module vérifie : présence d'un manifeste C2PA, intégrité de sa signature,
émetteur du certificat, et le type de source déclaré (digitalSourceType) par l'outil
qui a signé. Rappel : l'absence de signature ne signifie pas que le contenu est artificiel.
"""
import io
import json
from dataclasses import dataclass, field

import c2pa

IPTC = "http://cv.iptc.org/newscodes/digitalsourcetype/"
AI_SOURCE_TYPES = {
    "trainedAlgorithmicMedia": "créé par une IA générative",
    "compositeWithTrainedAlgorithmicMedia": "composé en partie avec une IA générative",
    "compositeSynthetic": "composé d'éléments synthétiques",
}
CAPTURE_SOURCE_TYPES = {
    "digitalCapture": "capturé par un appareil photo",
    "computationalCapture": "capturé par un appareil photo avec traitement automatique",
}

# Pas de téléchargement de manifestes distants : le serveur n'ouvre jamais une adresse
# fournie par un fichier inconnu.
_CTX = c2pa.Context.from_dict({"verify": {"remote_manifest_fetch": False}})


@dataclass
class ProvenanceReport:
    status: str  # "absent" | "remote_not_checked" | "invalid" | "valid" | "trusted" | "error"
    issuer: str | None = None
    generator: str | None = None
    ai_declarations: list[str] = field(default_factory=list)
    capture_declarations: list[str] = field(default_factory=list)


def _source_types(manifest_store: dict) -> list[str]:
    found = []
    for manifest in manifest_store.get("manifests", {}).values():
        for assertion in manifest.get("assertions", []):
            if not assertion.get("label", "").startswith("c2pa.actions"):
                continue
            for action in assertion.get("data", {}).get("actions", []):
                dst = action.get("digitalSourceType", "")
                if dst.startswith(IPTC):
                    found.append(dst[len(IPTC):])
    return found


def check(data: bytes, mime: str) -> ProvenanceReport:
    try:
        reader = c2pa.Reader(mime, io.BytesIO(data), context=_CTX)
    except Exception as exc:  # noqa: BLE001
        name = type(exc).__name__
        if "ManifestNotFound" in name or "no JUMBF" in str(exc):
            return ProvenanceReport(status="absent")
        if "remote" in str(exc).lower():
            return ProvenanceReport(status="remote_not_checked")
        return ProvenanceReport(status="error")

    try:
        state = (reader.get_validation_state() or "").lower()
        store = json.loads(reader.json())
    finally:
        reader.close()

    active = store.get("manifests", {}).get(store.get("active_manifest", ""), {})
    sig = active.get("signature_info") or {}
    gen_info = active.get("claim_generator_info") or []
    generator = active.get("claim_generator") or (gen_info[0].get("name") if gen_info else None)

    types = _source_types(store)
    report = ProvenanceReport(
        status={"trusted": "trusted", "valid": "valid"}.get(state, "invalid"),
        issuer=sig.get("issuer"),
        generator=generator,
        ai_declarations=sorted({AI_SOURCE_TYPES[t] for t in types if t in AI_SOURCE_TYPES}),
        capture_declarations=sorted({CAPTURE_SOURCE_TYPES[t] for t in types if t in CAPTURE_SOURCE_TYPES}),
    )
    return report
