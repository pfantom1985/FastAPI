from fastapi import APIRouter
from app.api.v1.endpoints import health, posts, upstream

router = APIRouter(prefix="/api/v1")

router.include_router(health.router, tags=["health"])
router.include_router(posts.router, tags=["posts"])
router.include_router(upstream.router, tags=["upstream"])
