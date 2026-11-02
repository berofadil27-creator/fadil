"""Vérification du format, de la taille et de la sécurité (cahier, section 6.1, étape 2).
Le type réel est déterminé par la signature du fichier, pas par son nom."""
from app.core import config
from app.core.errors import VeyraError


def sniff_type(data: bytes) -> str | None:
    head = data[:32]
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    if head.startswith(b"\x1a\x45\xdf\xa3"):
        return "video/webm"
    if head[4:8] == b"ftyp":
        brand = head[8:12]
        if brand in (b"heic", b"heix", b"hevc", b"heim", b"heis", b"mif1", b"msf1"):
            return "image/heic"
        if brand == b"qt  ":
            return "video/quicktime"
        return "video/mp4"
    return None


def _mb(n: int) -> str:
    return f"{n / (1024 * 1024):.0f} Mo"


def validate_text(text: str) -> str:
    clean = text.strip()
    if len(clean) < config.TEXT_MIN_CHARS:
        raise VeyraError(422, "text_too_short",
            f"Le texte est trop court ({len(clean)} caractères). Minimum : {config.TEXT_MIN_CHARS}.")
    if len(clean) > config.TEXT_MAX_CHARS:
        raise VeyraError(413, "text_too_long",
            f"Le texte est trop long ({len(clean)} caractères). Maximum : {config.TEXT_MAX_CHARS}.")
    return clean


def validate_file(data: bytes, kind: str) -> str:
    if not data:
        raise VeyraError(422, "empty_file", "Le fichier est vide.")
    allowed = config.IMAGE_TYPES if kind == "image" else config.VIDEO_TYPES
    limit = config.IMAGE_MAX_BYTES if kind == "image" else config.VIDEO_MAX_BYTES
    if len(data) > limit:
        raise VeyraError(413, "file_too_large", f"Le fichier dépasse la taille maximale ({_mb(limit)}).")
    mime = sniff_type(data)
    if mime not in allowed:
        label = "une photo (JPEG, PNG, WebP, HEIC)" if kind == "image" else "une vidéo (MP4, MOV, WebM)"
        raise VeyraError(415, "unsupported_format", f"Format non reconnu : le fichier doit être {label}.")
    return mime
