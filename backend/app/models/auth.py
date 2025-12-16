from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import relationship

from ..core.database import Base


# SQLAlchemy Models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    plots = relationship("Plot", back_populates="owner", cascade="all, delete-orphan")


class Plot(Base):
    __tablename__ = "plots"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    plot_data = Column(JSON, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="plots")


# Pydantic Models
class TokenRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    secret_key: str


class TokenResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlotCreate(BaseModel):
    title: str
    description: str = ""
    plot_data: dict


class PlotUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    plot_data: dict | None = None


class PlotResponse(BaseModel):
    id: int
    title: str
    description: str
    plot_data: dict
    user_id: int
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
