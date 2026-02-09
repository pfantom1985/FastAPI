from pydantic import BaseModel, ConfigDict

class UpstreamPingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
