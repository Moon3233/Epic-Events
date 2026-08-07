"""Exceptions et utilitaires partagés par la CLI."""

from __future__ import annotations

from datetime import datetime
from functools import wraps
from typing import Callable, ParamSpec, TypeVar

import click
from rich.console import Console

from epic_events.auth.session import AuthenticationError, AuthorizationError
from epic_events.services.clients import ClientError
from epic_events.services.contracts import ContractError
from epic_events.services.employees import EmployeeError
from epic_events.services.events import EventError

console = Console()

ServiceError = (
    AuthenticationError,
    AuthorizationError,
    EmployeeError,
    ClientError,
    ContractError,
    EventError,
    ValueError,
    click.ClickException,
)

P = ParamSpec("P")
R = TypeVar("R")


def handle_errors(func: Callable[P, R]) -> Callable[P, R]:
    """Affiche les erreurs métier proprement et quitte avec le code 1."""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except ServiceError as exc:
            console.print(f"[bold red]Erreur :[/bold red] {exc}")
            raise SystemExit(1) from exc

    return wrapper


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


def optional_text(value: str | None) -> str | None:
    """Normalise une saisie optionnelle (chaîne vide → None)."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
