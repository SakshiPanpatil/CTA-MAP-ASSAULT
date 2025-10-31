from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TokenRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    secret_key: str


class TokenResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
