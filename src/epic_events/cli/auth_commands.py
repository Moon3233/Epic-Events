"""Commandes d'authentification."""

from __future__ import annotations

import click

from epic_events.auth.session import get_current_identity, login, logout
from epic_events.cli import display
from epic_events.cli.utils import handle_errors
from epic_events.db import session_scope


@click.command("login")
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True)
@handle_errors
def login_cmd(email: str, password: str) -> None:
    """S'authentifier et stocker un jeton JWT."""
    with session_scope() as session:
        identity = login(session, email=email, password=password)
    display.success(f"Connecté : {identity.full_name} ({identity.department})")


@click.command("logout")
@handle_errors
def logout_cmd() -> None:
    """Supprimer le jeton local."""
    logout()
    display.success("Déconnecté.")


@click.command("whoami")
@handle_errors
def whoami_cmd() -> None:
    """Afficher la session courante."""
    with session_scope() as session:
        identity = get_current_identity(session)
    display.render_identity(identity)
