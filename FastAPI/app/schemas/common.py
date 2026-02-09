from typing import Any, Optional
from pydantic import BaseModel

class ErrorInfo(BaseModel):
    code: str
    message: str
    details: Optional[dict[str, Any]] = None

class ErrorResponse(BaseModel):
    error: ErrorInfo
