from contextlib import asynccontextmanager
import logging

import requests
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import router as v1_router
from app.core.logging import setup_logging
from app.core.middleware import request_id_middleware


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    app.state.http_session = requests.Session()
    try:
        yield
    finally:
        app.state.http_session.close()


app = FastAPI(
    title="Proxy & Contract API",
    lifespan=lifespan,
)

# Middleware подключаем сразу после создания app — это нормальная практика. [web:333]
app.middleware("http")(request_id_middleware)

# Роутеры можно подключать до/после exception handlers — оба варианта рабочие.
app.include_router(v1_router)


def error_payload(code: str, message: str, details: dict | None = None) -> dict:
    payload = {"error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return payload


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Единый формат ответа на HTTP ошибки (включая 404). [web:1]
    if isinstance(exc.detail, dict) and "code" in exc.detail and "message" in exc.detail:
        details = exc.detail.get("details")
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(
                code=str(exc.detail["code"]),
                message=str(exc.detail["message"]),
                details=details if isinstance(details, dict) or details is None else {"value": details},
            ),
        )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(code="HTTP_ERROR", message=str(exc.detail)),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=error_payload(
            code="VALIDATION_ERROR",
            message="Validation error",
            details={"errors": exc.errors()},
        ),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Важно: логируем, но наружу всё равно отдаём контрактный ответ 500. [web:1]
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content=error_payload(code="INTERNAL_ERROR", message="Internal server error"),
    )
