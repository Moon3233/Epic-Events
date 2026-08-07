"""Persistance locale du jeton JWT (fichier dédié, hors dépôt)."""

from __future__ import annotations

from pathlib import Path

# Fichier dans le home utilisateur : portable et hors du repo git
TOKEN_DIR = Path.home() / ".epic_events"
TOKEN_PATH = TOKEN_DIR / "token"


def save_token(token: str) -> Path:
    """Enregistre le jeton avec des permissions restrictives (0600)."""
    TOKEN_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    TOKEN_PATH.write_text(token, encoding="utf-8")
    TOKEN_PATH.chmod(0o600)
    return TOKEN_PATH


def load_token() -> str | None:
    """Lit le jeton local, ou None s'il est absent."""
    if not TOKEN_PATH.is_file():
        return None
    content = TOKEN_PATH.read_text(encoding="utf-8").strip()
    return content or None


def clear_token() -> None:
    """Supprime le jeton local (logout)."""
    if TOKEN_PATH.is_file():
        TOKEN_PATH.unlink()
