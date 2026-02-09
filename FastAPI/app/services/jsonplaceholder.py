from __future__ import annotations
import logging
from typing import Any
from fastapi import HTTPException
from pydantic import ValidationError
from app.clients.http import HttpClient, UpstreamHTTPError, UpstreamTimeoutError
from app.core.config import Settings
from app.schemas.posts import Comment, Post, PostWithComments

logger = logging.getLogger(__name__)

class JsonPlaceholderService:
    def __init__(self, client: HttpClient, settings: Settings):
        self._client = client
        self._base_url = settings.JSONPLACEHOLDER_BASE_URL.rstrip("/")

    # ---- Public API (возвращаем уже нормализованные модели) ----
    def list_posts(self, *, limit: int, start: int) -> list[Post]:
        url = f"{self._base_url}/posts"
        resp = self._safe_get(url, params={"_limit": limit, "_start": start})
        data = self._parse_json(resp, expected="list_posts")
        return self._validate_posts_list(data)

    def get_post(self, *, post_id: int) -> Post:
        url = f"{self._base_url}/posts/{post_id}"
        resp = self._safe_get(
            url,
            params=None,
            not_found_code="NOT_FOUND",
            not_found_message="Post not found",
        )
        data = self._parse_json(resp, expected="get_post")
        return self._validate_post(data)

    def list_comments(self, *, post_id: int) -> list[Comment]:
        url = f"{self._base_url}/posts/{post_id}/comments"
        resp = self._safe_get(url, params=None)
        data = self._parse_json(resp, expected="list_comments")
        return self._validate_comments_list(data)

    def get_post_with_comments(self, *, post_id: int) -> PostWithComments:
        post = self.get_post(post_id=post_id)
        comments = self.list_comments(post_id=post_id)
        return PostWithComments(post=post, comments=comments, comments_count=len(comments))

    def search_posts(self, *, q: str, limit: int, start: int) -> list[Post]:
        posts = self.list_posts(limit=limit, start=start)
        q_lower = q.lower()
        return [p for p in posts if q_lower in p.title.lower()]

    # ---- Transport / errors mapping ----
    def _safe_get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None,
        not_found_code: str | None = None,
        not_found_message: str | None = None,
    ):
        try:
            resp = self._client.request("GET", url, params=params)
        except UpstreamTimeoutError as exc:
            raise HTTPException(
                status_code=504,
                detail={
                    "code": "UPSTREAM_TIMEOUT",
                    "message": "Upstream timeout",
                    "details": {"upstream": "jsonplaceholder"},
                },
            ) from exc
        except UpstreamHTTPError as exc:
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "UPSTREAM_ERROR",
                    "message": "Upstream service error",
                    "details": {"upstream_status": exc.status_code, "upstream": "jsonplaceholder"},
                },
            ) from exc

        if resp.status_code == 404 and not_found_code and not_found_message:
            raise HTTPException(
                status_code=404,
                detail={"code": not_found_code, "message": not_found_message},
            )
        return resp

    def _parse_json(self, resp, *, expected: str):
        try:
            return resp.json()
        except ValueError as exc:
            logger.warning("upstream_bad_json expected=%s status=%s", expected, resp.status_code)
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "UPSTREAM_BAD_RESPONSE",
                    "message": "Upstream returned invalid JSON",
                    "details": {"upstream": "jsonplaceholder"},
                },
            ) from exc

    # ---- Pydantic validation (UPSTREAM_BAD_RESPONSE) ----
    def _upstream_validation_failed(self, *, expected: str, exc: ValidationError) -> HTTPException:
        # Не отдаём “внутренности” слишком подробно; errors() достаточно для дебага формата
        return HTTPException(
            status_code=502,
            detail={
                "code": "UPSTREAM_BAD_RESPONSE",
                "message": "Upstream response validation failed",
                "details": {"expected": expected, "errors": exc.errors()},
            },
        )

    def _validate_post(self, data: Any) -> Post:
        try:
            return Post.model_validate(data)
        except ValidationError as exc:
            raise self._upstream_validation_failed(expected="Post", exc=exc) from exc

    def _validate_posts_list(self, data: Any) -> list[Post]:
        if not isinstance(data, list):
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "UPSTREAM_BAD_RESPONSE",
                    "message": "Upstream returned unexpected JSON type",
                    "details": {"expected": "list[Post]"},
                },
            )
        try:
            return [Post.model_validate(item) for item in data]
        except ValidationError as exc:
            raise self._upstream_validation_failed(expected="list[Post]", exc=exc) from exc

    def _validate_comments_list(self, data: Any) -> list[Comment]:
        if not isinstance(data, list):
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "UPSTREAM_BAD_RESPONSE",
                    "message": "Upstream returned unexpected JSON type",
                    "details": {"expected": "list[Comment]"},
                },
            )
        try:
            return [Comment.model_validate(item) for item in data]
        except ValidationError as exc:
            raise self._upstream_validation_failed(expected="list[Comment]", exc=exc) from exc
