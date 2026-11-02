"""Stockage des analyses EN MÉMOIRE (provisoire).
Les résultats disparaissent au redémarrage du serveur. Remplacé par PostgreSQL / Supabase
dans une phase suivante. Aucun fichier n'est conservé : seul le rapport est gardé."""
from threading import Lock
from app.schemas.analysis import AnalysisResult

_lock = Lock()
_records: dict[str, tuple[str, AnalysisResult]] = {}  # id -> (client_id, résultat)


def save(client_id: str, result: AnalysisResult) -> None:
    with _lock:
        _records[result.analysis_id] = (client_id, result)


def get(client_id: str, analysis_id: str) -> AnalysisResult | None:
    with _lock:
        rec = _records.get(analysis_id)
    if rec is None or rec[0] != client_id:  # droits : on ne voit que ses propres analyses
        return None
    return rec[1]


def history(client_id: str) -> list[AnalysisResult]:
    with _lock:
        items = [r for c, r in _records.values() if c == client_id]
    return sorted(items, key=lambda r: r.created_at, reverse=True)


def delete(client_id: str, analysis_id: str) -> bool:
    with _lock:
        rec = _records.get(analysis_id)
        if rec is None or rec[0] != client_id:
            return False
        del _records[analysis_id]
        return True


def clear() -> None:
    with _lock:
        _records.clear()
