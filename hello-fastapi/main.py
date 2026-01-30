from fastapi import FastAPI
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi import Request
from fastapi.exceptions import RequestValidationError

app = FastAPI(
    title="Hello, FastAPI World",
    version="1.0.0",
)

class HelloResponse(BaseModel):
    message: str
    timestamp: str
    version: str

class EchoRequest(BaseModel):
    name: str = Field(min_length=1)
    age: int = Field(ge=0, le=120)

class EchoResponse(BaseModel):
    greeting: str
    adult: bool
    status: str

class EchoNameResponse(BaseModel):
    message: str
    uppercase: str

class SecretResponse(BaseModel):
    secret: str


class ErrorResponse(BaseModel):
    error: str
    code: str

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    parts: list[str] = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        parts.append(f"{loc}: {msg}")
    message = "; ".join(parts) if parts else "Validation error"
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error=message,
            code="VALIDATION_ERROR",
        ).model_dump(),
    )

@app.get("/", response_model=HelloResponse)
def root() -> HelloResponse:
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return HelloResponse(
        message="Hello, FastAPI!",
        timestamp=timestamp,
        version="1.0.0",
    )

@app.post(
    "/echo",
    response_model=EchoResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
    },
)
def echo(payload: EchoRequest) -> EchoResponse:
    return EchoResponse(
        greeting=f"Привет, {payload.name}!",
        adult=payload.age >= 18,
        status="success",
    )

@app.get("/echo/{name}", response_model=EchoNameResponse)
def echo_name(name: str) -> EchoNameResponse:
    return EchoNameResponse(
        message=f"Привет, {name}!",
        uppercase=name.upper(),
    )

@app.get(
    "/secret/{token}",
    response_model=SecretResponse,
    responses={
        401: {"model": ErrorResponse},
    },
)
def secret(token: str):
    if token == "admin":
        return SecretResponse(secret="Секретный доступ открыт!")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=ErrorResponse(
            error="Доступ запрещён",
            code="INVALID_TOKEN",
        ).model_dump(),
    )
