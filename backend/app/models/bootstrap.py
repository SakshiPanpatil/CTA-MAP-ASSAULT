from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

from .gtfs import BootstrapPayload


class BootstrapProgress(BaseModel):
    model_config = ConfigDict(extra="ignore")

    step: str
    status: Literal["pending", "active", "complete", "error"]


class BootstrapResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Literal["warming", "ready", "error"]
    progress: list[BootstrapProgress]
    payload: Optional[BootstrapPayload] = None
    message: Optional[str] = None
