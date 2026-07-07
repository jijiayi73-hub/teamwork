from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    return settings.database_url


def get_sqlite_path() -> Path | None:
    database_url = get_database_url()
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None

    raw_path = database_url[len(prefix) :]
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def ensure_sqlite_parent_directory() -> None:
    database_path = get_sqlite_path()
    if database_path is not None:
        database_path.parent.mkdir(parents=True, exist_ok=True)


ensure_sqlite_parent_directory()
engine = create_engine(
    get_database_url(),
    connect_args={"check_same_thread": False} if get_database_url().startswith("sqlite:///") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    if get_database_url().startswith("sqlite:///"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_database() -> None:
    from . import models

    Base.metadata.create_all(bind=engine)
