from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "backend" / "app" / "templates"


class Settings(BaseSettings):
    """Application-wide configuration managed via environment variables."""

    app_name: str = "CTA Map Assault API"
    version: str = "0.1.0"
    api_prefix: str = "/api"
    data_directory: Path = DATA_DIR
    templates_directory: Path = TEMPLATES_DIR

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance so expensive parsing occurs once."""
    return Settings()


settings = get_settings()
