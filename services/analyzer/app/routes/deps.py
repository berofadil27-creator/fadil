import re
from fastapi import Header
from app.core.errors import VeyraError

_ID = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


def client_id(x_client_id: str | None = Header(default=None)) -> str:
    """Identifiant anonyme du navigateur, en attendant les comptes (Supabase Auth).
    Il sert à séparer les historiques ; ce n'est PAS une authentification."""
    if not x_client_id or not _ID.match(x_client_id):
        raise VeyraError(400, "missing_client_id", "Identifiant client manquant ou invalide.")
    return x_client_id
