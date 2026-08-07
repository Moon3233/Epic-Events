"""Commandes collaborateurs (gestion)."""

from __future__ import annotations

import click

from epic_events.cli import display
from epic_events.cli.utils import handle_errors, optional_text
from epic_events.db import session_scope
from epic_events.services.employees import (
    create_collaborator,
    delete_collaborator,
    list_employees,
    update_collaborator,
)


@click.group("employees")
def employees_group() -> None:
    """Gérer les collaborateurs."""


@employees_group.command("list")
@handle_errors
def employees_list() -> None:
    """Lister les collaborateurs."""
    with session_scope() as session:
        display.render_employees(list_employees(session))


@employees_group.command("create")
@click.option("--number", "employee_number", prompt="N° employé")
@click.option("--name", "full_name", prompt="Nom complet")
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@click.option(
    "--department",
    prompt="Département",
    type=click.Choice(["gestion", "commercial", "support"], case_sensitive=False),
)
@handle_errors
def employees_create(
    employee_number: str,
    full_name: str,
    email: str,
    password: str,
    department: str,
) -> None:
    """Créer un collaborateur."""
    with session_scope() as session:
        identity = create_collaborator(
            session,
            employee_number=employee_number,
            full_name=full_name,
            email=email,
            password=password,
            department_name=department.lower(),
        )
    display.success(f"Collaborateur créé #{identity.id} — {identity.full_name}")


@employees_group.command("update")
@click.argument("employee_id", type=int)
@click.option("--number", "employee_number", default=None, help="Nouveau n°")
@click.option("--name", "full_name", default=None, help="Nouveau nom")
@click.option("--email", default=None, help="Nouvel email")
@click.option("--password", default=None, help="Nouveau mot de passe")
@click.option(
    "--department",
    default=None,
    type=click.Choice(["gestion", "commercial", "support"], case_sensitive=False),
)
@handle_errors
def employees_update(
    employee_id: int,
    employee_number: str | None,
    full_name: str | None,
    email: str | None,
    password: str | None,
    department: str | None,
) -> None:
    """Mettre à jour un collaborateur."""
    with session_scope() as session:
        identity = update_collaborator(
            session,
            employee_id,
            employee_number=optional_text(employee_number),
            full_name=optional_text(full_name),
            email=optional_text(email),
            password=optional_text(password),
            department_name=department.lower() if department else None,
        )
    display.success(f"Collaborateur #{identity.id} mis à jour.")


@employees_group.command("delete")
@click.argument("employee_id", type=int)
@click.confirmation_option(prompt="Confirmer la suppression ?")
@handle_errors
def employees_delete(employee_id: int) -> None:
    """Supprimer un collaborateur."""
    with session_scope() as session:
        delete_collaborator(session, employee_id)
    display.success(f"Collaborateur #{employee_id} supprimé.")
