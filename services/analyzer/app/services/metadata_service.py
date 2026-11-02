"""Lecture des métadonnées d'une photo (EXIF, blocs texte PNG, XMP).

Les métadonnées se modifient ou se suppriment facilement : elles donnent des indices,
jamais des preuves. Les réseaux sociaux les suppriment souvent."""
import io
import re
from dataclasses import dataclass, field

from PIL import ExifTags, Image

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except Exception:  # noqa: BLE001
    pass

# Noms d'outils de génération qui s'inscrivent parfois eux-mêmes dans les métadonnées.
AI_TOOL_PATTERNS = {
    "Stable Diffusion": r"stable[\s_-]?diffusion|automatic1111|sd[\s_-]?webui",
    "ComfyUI": r"comfyui",
    "Midjourney": r"midjourney",
    "DALL·E": r"dall[·-]e",
    "Adobe Firefly": r"firefly",
    "NovelAI": r"novelai",
    "Leonardo.Ai": r"leonardo\.?ai",
}
# Blocs texte typiques des images Stable Diffusion / ComfyUI (paramètres de génération).
GENERATION_KEYS = {"parameters", "prompt", "workflow", "negative_prompt", "sd-metadata", "dream"}
XMP_AI_TYPES = ("trainedAlgorithmicMedia", "compositeWithTrainedAlgorithmicMedia")


@dataclass
class MetadataReport:
    readable: bool
    width: int | None = None
    height: int | None = None
    camera: str | None = None
    software: str | None = None
    date_taken: str | None = None
    ai_tools: list[str] = field(default_factory=list)
    generation_params: bool = False
    xmp_ai_declared: bool = False
    has_any: bool = False


def _find_tools(text: str) -> set[str]:
    return {name for name, pat in AI_TOOL_PATTERNS.items() if re.search(pat, text, re.I)}


def read(data: bytes) -> MetadataReport:
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception:  # noqa: BLE001
        return MetadataReport(readable=False)

    rep = MetadataReport(readable=True, width=img.width, height=img.height)
    tools: set[str] = set()

    exif = img.getexif()
    if exif:
        tags = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
        try:
            tags.update({ExifTags.TAGS.get(k, k): v for k, v in exif.get_ifd(ExifTags.IFD.Exif).items()})
        except Exception:  # noqa: BLE001
            pass
        make, model = str(tags.get("Make", "")).strip(), str(tags.get("Model", "")).strip()
        if make or model:
            rep.camera = model if make and model.lower().startswith(make.lower()) else f"{make} {model}".strip()
        if tags.get("Software"):
            rep.software = str(tags["Software"]).strip()[:120]
        if tags.get("DateTimeOriginal"):
            rep.date_taken = str(tags["DateTimeOriginal"]).strip()
        for key in ("Software", "Artist", "ImageDescription", "UserComment", "Make"):
            if tags.get(key):
                tools |= _find_tools(str(tags[key]))

    # Blocs texte (PNG) et autres infos
    for key, value in (img.info or {}).items():
        if not isinstance(key, str):
            continue
        if key.lower() in GENERATION_KEYS:
            rep.generation_params = True
        if isinstance(value, (str, bytes)):
            text = value.decode("utf-8", "ignore") if isinstance(value, bytes) else value
            if key.lower() in ("software", "comment", "description", "parameters", "xml:com.adobe.xmp"):
                tools |= _find_tools(text[:20000])
            if "xmp" in key.lower() and any(t in text for t in XMP_AI_TYPES):
                rep.xmp_ai_declared = True

    # XMP intégré (JPEG, WebP…) : lu directement dans le fichier.
    start = data.find(b"<x:xmpmeta")
    if start != -1:
        end = data.find(b"</x:xmpmeta>", start)
        xmp_text = data[start:end if end != -1 else start + 200_000].decode("utf-8", "ignore")
        if any(t in xmp_text for t in XMP_AI_TYPES):
            rep.xmp_ai_declared = True
        tools |= _find_tools(xmp_text[:20000])

    rep.ai_tools = sorted(tools)
    rep.has_any = bool(rep.camera or rep.software or rep.date_taken or rep.ai_tools
                       or rep.generation_params or rep.xmp_ai_declared)
    return rep
