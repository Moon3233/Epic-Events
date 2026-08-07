"""Commande d'initialisation de la base."""

from __future__ import annotations

import click

from epic_events.cli import display
from epic_events.cli.utils import handle_errors
from epic_events.db import check_connection, init_db, session_scope
from epic_events.services.employees import create_employee, get_employee_by_email


@click.command("init-db")
@handle_errors
def init_db_cmd() -> None:
    """Créer les tables et les départements (gestion, commercial, support)."""
    display.info(check_connection())
    init_db()
    display.success("Base initialisée (tables + départements).")


@click.command("seed-admin")
@click.option("--number", default="G001", show_default=True)
@click.option("--name", default="Admin Gestion", show_default=True)
@click.option("--email", default="admin@epic-events.local", show_default=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@handle_errors
def seed_admin_cmd(number: str, name: str, email: str, password: str) -> None:
    """Créer un premier compte gestion (si l'email n'existe pas encore)."""
    with session_scope() as session:
        if get_employee_by_email(session, email) is not None:
            display.info(f"Le compte {email} existe déjà.")
            return
        identity = create_employee(
            session,
            employee_number=number,
            full_name=name,
            email=email,
            password=password,
            department_name="gestion",
        )
    display.success(
        f"Compte gestion créé #{identity.id} — {identity.email} "
        "(utilisez `login` ensuite)."
    )
