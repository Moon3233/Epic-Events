"""Connexion à PostgreSQL via SQLAlchemy 2.x."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from epic_events.config import get_database_settings

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Singleton Engine — une seule pool de connexions pour l'application."""
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_database_settings()
        _engine = create_engine(
            settings.url,
            pool_pre_ping=True,  # détecte les connexions mortes
            echo=False,
        )
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Retourne la factory de sessions (crée l'engine si besoin)."""
    get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager : commit si OK, rollback sinon, fermeture toujours."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_connection() -> str:
    """Ping SQL simple pour valider la connexion à la base."""
    with get_engine().connect() as connection:
        result = connection.execute(text("SELECT current_user, current_database()"))
        user, database = result.one()
        return f"Connecté en tant que « {user} » sur la base « {database} »."
