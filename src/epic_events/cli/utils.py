"""Helpers d'affichage et de parsing pour la CLI."""

from __future__ import annotations

import sys
from datetime import datetime


def print_error(exc: Exception) -> None:
    print(f"Erreur : {exc}", file=sys.stderr)


def parse_datetime(value: str) -> datetime:
    """Accepte 'YYYY-MM-DD HH:MM' ou 'YYYY-MM-DD'."""
    value = value.strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(
        "Date invalide. Formats acceptés : YYYY-MM-DD HH:MM ou YYYY-MM-DD."
    )


def prompt(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{label}{suffix} : ").strip()
    if not value and default is not None:
        return default
    return value


def prompt_optional(label: str) -> str | None:
    value = input(f"{label} (vide = inchangé) : ").strip()
    return value or None
