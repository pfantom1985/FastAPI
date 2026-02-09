from fastapi import APIRouter, Depends
from app.core.deps import get_jsonplaceholder_service
from app.schemas.upstream import UpstreamPingResponse
from app.services.jsonplaceholder import JsonPlaceholderService

router = APIRouter(prefix="/upstream")

@router.get("/ping", response_model=UpstreamPingResponse)
def upstream_ping(service: JsonPlaceholderService = Depends(get_jsonplaceholder_service)):
    service.list_posts(limit=1, start=0)
    return UpstreamPingResponse(status="upstream ok")
