from fastapi import APIRouter, Depends
from fastapi.responses import Response
from app.core.errors import VeyraError
from app.routes.deps import client_id
from app.schemas.analysis import AnalysisResult, HistoryItem, HistoryResponse
from app.services import store

router = APIRouter(prefix="/api", tags=["résultats"])

NOT_FOUND = VeyraError(404, "analysis_not_found", "Analyse introuvable.")


@router.get("/analysis/{analysis_id}", response_model=AnalysisResult, summary="Consulter un résultat")
def get_analysis(analysis_id: str, cid: str = Depends(client_id)):
    result = store.get(cid, analysis_id)
    if result is None:
        raise NOT_FOUND
    return result


@router.get("/history", response_model=HistoryResponse, summary="Consulter son historique")
def get_history(cid: str = Depends(client_id)):
    items = [HistoryItem(**r.model_dump(include={"analysis_id", "content_type", "status",
                                                  "conclusion", "created_at"}))
             for r in store.history(cid)]
    return HistoryResponse(items=items, persistent=False)


@router.delete("/analysis/{analysis_id}", status_code=204, summary="Supprimer une analyse")
def delete_analysis(analysis_id: str, cid: str = Depends(client_id)):
    if not store.delete(cid, analysis_id):
        raise NOT_FOUND
    return Response(status_code=204)
