from fastapi import APIRouter, Depends, File, Form, UploadFile
from app.core import config
from app.core.errors import VeyraError
from app.detectors import image_detector, text_detector, video_detector
from app.routes.deps import client_id
from app.schemas.analysis import AnalysisResult, TextRequest
from app.services import file_validation, orchestrator, rate_limit

router = APIRouter(prefix="/api/analyze", tags=["analyse"])


async def _read(upload: UploadFile, limit: int) -> bytes:
    data = await upload.read(limit + 1)
    if len(data) > limit:
        raise VeyraError(413, "file_too_large", "Le fichier dépasse la taille maximale.")
    return data


@router.post("/text", response_model=AnalysisResult, summary="Analyser un texte")
def analyze_text(body: TextRequest, cid: str = Depends(client_id)):
    text = file_validation.validate_text(body.text)
    rate_limit.check(cid)
    return orchestrator.run(cid, "text", lambda: text_detector.analyze(text))


@router.post("/image", response_model=AnalysisResult, summary="Analyser une photo")
async def analyze_image(file: UploadFile = File(...), cid: str = Depends(client_id)):
    data = await _read(file, config.IMAGE_MAX_BYTES)
    mime = file_validation.validate_file(data, "image")
    rate_limit.check(cid)
    return orchestrator.run(cid, "image", lambda: image_detector.analyze(data, mime))


@router.post("/video", response_model=AnalysisResult,
             summary="Analyser une vidéo (images extraites par le navigateur)")
async def analyze_video(frames: list[UploadFile] = File(...), timestamps: str = Form(...),
                        duration: float | None = Form(None), cid: str = Depends(client_id)):
    if not config.VIDEO_FRAMES_MIN <= len(frames) <= config.VIDEO_FRAMES_MAX:
        raise VeyraError(422, "bad_frames",
                         f"Il faut entre {config.VIDEO_FRAMES_MIN} et {config.VIDEO_FRAMES_MAX} images extraites.")
    data = [await _read(f, config.FRAME_MAX_BYTES) for f in frames]
    for d in data:
        if file_validation.sniff_type(d) != "image/jpeg":
            raise VeyraError(415, "unsupported_format", "Les images extraites doivent être au format JPEG.")
    try:
        ts = [float(x) for x in timestamps.split(",")]
    except ValueError:
        raise VeyraError(422, "bad_frames", "Horodatages des images invalides.")
    if len(ts) != len(data):
        raise VeyraError(422, "bad_frames", "Chaque image doit avoir un horodatage.")
    rate_limit.check(cid)
    return orchestrator.run(cid, "video", lambda: video_detector.analyze(data, ts, duration))
