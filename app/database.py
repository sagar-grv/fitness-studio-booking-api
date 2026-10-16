"""Database engine and session setup (SQLAlchemy + SQLite)."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import DATABASE_URL

# check_same_thread is required for SQLite with FastAPI's threadpool.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
