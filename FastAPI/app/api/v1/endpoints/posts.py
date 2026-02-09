from __future__ import annotations
from fastapi import APIRouter, Depends, Path, Query
from app.core.deps import get_jsonplaceholder_service
from app.schemas.posts import Post, PostWithComments
from app.services.jsonplaceholder import JsonPlaceholderService

router = APIRouter(prefix="/posts")

@router.get("/search", response_model=list[Post])
def search_posts(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    start: int = Query(0, ge=0),
    service: JsonPlaceholderService = Depends(get_jsonplaceholder_service),
):
    return service.search_posts(q=q, limit=limit, start=start)

@router.get("", response_model=list[Post])
def list_posts(
    limit: int = Query(10, ge=1, le=50),
    start: int = Query(0, ge=0),
    service: JsonPlaceholderService = Depends(get_jsonplaceholder_service),
):
    return service.list_posts(limit=limit, start=start)

@router.get("/{post_id}", response_model=PostWithComments)
def get_post_with_comments(
    post_id: int = Path(..., ge=1),
    service: JsonPlaceholderService = Depends(get_jsonplaceholder_service),
):
    return service.get_post_with_comments(post_id=post_id)
