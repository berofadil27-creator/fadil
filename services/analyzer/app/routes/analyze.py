from fastapi import APIRouter, Depends, File, UploadFile
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
    return orchestrator.run(cid, "text", lambda: text_detector.analyze(text),
                            text_detector.DETECTION_AVAILABLE)


@router.post("/image", response_model=AnalysisResult, summary="Analyser une photo")
async def analyze_image(file: UploadFile = File(...), cid: str = Depends(client_id)):
    data = await _read(file, config.IMAGE_MAX_BYTES)
    mime = file_validation.validate_file(data, "image")
    rate_limit.check(cid)
    return orchestrator.run(cid, "image", lambda: image_detector.analyze(data, mime),
                            image_detector.DETECTION_AVAILABLE)


@router.post("/video", response_model=AnalysisResult, summary="Analyser une vidéo")
async def analyze_video(file: UploadFile = File(...), cid: str = Depends(client_id)):
    data = await _read(file, config.VIDEO_MAX_BYTES)
    mime = file_validation.validate_file(data, "video")
    rate_limit.check(cid)
    return orchestrator.run(cid, "video", lambda: video_detector.analyze(data, mime),
                            video_detector.DETECTION_AVAILABLE)
