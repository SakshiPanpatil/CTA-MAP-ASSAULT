import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,   # test connections before use; discards stale ones
    pool_recycle=300,     # recycle connections every 5 min to avoid Neon timeouts
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Database session with automatic retry for Neon cold-start delays."""
    max_retries = 3
    delay = 1.0
    last_exc: Exception | None = None

    for attempt in range(max_retries):
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))  # wake up Neon compute if paused
            break
        except OperationalError as exc:
            db.close()
            last_exc = exc
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
    else:
        raise last_exc  # type: ignore[misc]

    try:
        yield db
    finally:
        db.close()
