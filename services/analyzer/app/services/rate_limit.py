"""Limite d'utilisation simple, par client et par heure (en mémoire, provisoire)."""
import time
from collections import defaultdict, deque
from threading import Lock
from app.core import config
from app.core.errors import VeyraError

_lock = Lock()
_hits: dict[str, deque] = defaultdict(deque)


def check(client_id: str) -> None:
    now = time.time()
    with _lock:
        q = _hits[client_id]
        while q and now - q[0] > 3600:
            q.popleft()
        if len(q) >= config.RATE_LIMIT_PER_HOUR:
            raise VeyraError(429, "rate_limited",
                f"Limite atteinte : {config.RATE_LIMIT_PER_HOUR} analyses par heure. Réessayez plus tard.")
        q.append(now)


def reset() -> None:
    with _lock:
        _hits.clear()
