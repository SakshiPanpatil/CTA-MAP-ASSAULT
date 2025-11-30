from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status

from ....core.config import settings
from ....core.security import create_access_token
from ....models.auth import TokenRequest, TokenResponse

router = APIRouter()


@router.post("/token", response_model=TokenResponse)
def create_token(payload: TokenRequest) -> TokenResponse:
    if payload.secret_key != settings.access_passphrase:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access credentials",
        )

    expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    token = create_access_token("cta-map-client", expires_delta)
    expires_at = datetime.now(timezone.utc) + expires_delta
    return TokenResponse(access_token=token, expires_at=expires_at)
