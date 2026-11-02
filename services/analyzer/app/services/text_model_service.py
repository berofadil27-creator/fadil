"""Analyse de texte par un modèle open source hébergé sur un Hugging Face Space (Phase 5, expérimental).

Modèle : almanach/camemberta-chatgptdetect-noisy (français ; ses auteurs le réservent à la recherche).
Test interne (2026-11-02, 31 textes humains, 24 textes IA d'un seul générateur) : aucun texte humain
au-dessus de 0,16, mais 3 textes IA sous 0,01. Conséquences (seuils provisoires) :
- score >= HIGH : traces IA nettes ;
- score <= LOW : peu de traces, ce qui NE prouve PAS une origine humaine (le modèle rate des textes IA) ;
- sinon : incertain. Le score n'est jamais affiché.
"""
import os
from dataclasses import dataclass

import httpx

HIGH = float(os.getenv("VEYRA_TEXT_HIGH", "0.90"))
LOW = float(os.getenv("VEYRA_TEXT_LOW", "0.20"))


@dataclass
class TextModelReport:
    status: str  # "ok" | "unconfigured" | "error"
    level: str | None = None  # "high" | "low" | "uncertain"
    score: float | None = None  # gardé côté serveur


def analyze(text: str) -> TextModelReport:
    url, key = os.getenv("VEYRA_TEXT_DETECTOR_URL"), os.getenv("VEYRA_DETECTOR_KEY")
    if not url or not key:
        return TextModelReport(status="unconfigured")
    try:
        r = httpx.post(url.rstrip("/") + "/detect", json={"text": text},
                       headers={"x-veyra-key": key}, timeout=45.0)
        if r.status_code != 200:
            return TextModelReport(status="error")
        score = float(r.json()["score"])
    except Exception:  # noqa: BLE001
        return TextModelReport(status="error")
    level = "high" if score >= HIGH else "low" if score <= LOW else "uncertain"
    return TextModelReport(status="ok", level=level, score=score)
