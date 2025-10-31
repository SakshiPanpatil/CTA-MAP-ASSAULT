from collections.abc import Iterator
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .core.security import decode_access_token
from .services.gtfs_loader import GTFSDataLoader, get_default_loader

bearer_scheme = HTTPBearer(auto_error=False)


def get_loader() -> Iterator[GTFSDataLoader]:
    """FastAPI dependency that yields a reusable GTFS loader instance."""
    loader = get_default_loader()
    yield loader


def require_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    """Validate bearer token and return decoded payload."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)
