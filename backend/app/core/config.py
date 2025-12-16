from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "backend" / "app" / "templates"
STATIC_DIR = BASE_DIR / "backend" / "app" / "static"
ASSAULTS_FILE = BASE_DIR / "Cleaned_CTA_Bus_Data.csv"


class Settings(BaseSettings):
    """Application-wide configuration managed via environment variables."""

    app_name: str = "CTA Map Assault API"
    version: str = "0.1.0"
    api_prefix: str = "/api"
    data_directory: Path = DATA_DIR
    templates_directory: Path = TEMPLATES_DIR
    static_directory: Path = STATIC_DIR
    assault_data_file: Path = ASSAULTS_FILE
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    access_passphrase: str = Field(..., env="ACCESS_PASSPHRASE")
    # Local LLM (Ollama) configuration
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.1:8b", env="OLLAMA_MODEL")
    # Database configuration
    database_url: str = Field(..., env="DATABASE_URL")

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore legacy env vars like OPENAI_API_KEY


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance so expensive parsing occurs once."""
    return Settings()


settings = get_settings()
