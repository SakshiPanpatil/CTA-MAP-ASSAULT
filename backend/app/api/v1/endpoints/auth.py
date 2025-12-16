from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....core.config import settings
from ....core.database import get_db
from ....core.security import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from ....models.auth import (
    TokenRequest,
    TokenResponse,
    User,
    UserCreate,
    UserLogin,
    UserResponse,
)

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


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserCreate, db: Session = Depends(get_db)) -> TokenResponse:
    # Check if username already exists
    db_user = db.query(User).filter(User.username == user_data.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create access token
    expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    token = create_access_token(new_user.username, expires_delta)
    expires_at = datetime.now(timezone.utc) + expires_delta

    return TokenResponse(access_token=token, expires_at=expires_at)


@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    # Find user by username
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # Create access token
    expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    token = create_access_token(user.username, expires_delta)
    expires_at = datetime.now(timezone.utc) + expires_delta

    return TokenResponse(access_token=token, expires_at=expires_at)


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
