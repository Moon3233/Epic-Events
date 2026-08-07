"""Chargement de la configuration depuis les variables d'environnement."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

# Racine du dépôt (Epic-Events/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class DatabaseSettings:
    """Paramètres de connexion PostgreSQL (compte applicatif non privilégié)."""

    host: str
    port: int
    name: str
    user: str
    password: str

    @property
    def url(self) -> str:
        """URL SQLAlchemy (driver psycopg v3)."""
        user = quote_plus(self.user)
        password = quote_plus(self.password)
        return (
            f"postgresql+psycopg://{user}:{password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


def get_database_settings() -> DatabaseSettings:
    """Lit les variables DB_* ; lève une erreur claire si une clé manque."""
    required = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError(
            "Variables d'environnement manquantes : "
            + ", ".join(missing)
            + ". Copiez .env.example vers .env et renseignez les valeurs."
        )

    return DatabaseSettings(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        name=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )
