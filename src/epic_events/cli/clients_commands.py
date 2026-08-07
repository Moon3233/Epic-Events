"""Commandes clients."""

from __future__ import annotations

import click

from epic_events.cli import display
from epic_events.cli.utils import handle_errors, optional_text
from epic_events.db import session_scope
from epic_events.services.clients import create_client, list_clients, update_client


@click.group("clients")
def clients_group() -> None:
    """Gérer les clients."""


@clients_group.command("list")
@handle_errors
def clients_list() -> None:
    """Lister tous les clients."""
    with session_scope() as session:
        display.render_clients(list_clients(session))


@clients_group.command("create")
@click.option("--name", "full_name", prompt="Nom complet")
@click.option("--email", prompt=True)
@click.option("--phone", prompt="Téléphone")
@click.option("--company", "company_name", prompt="Entreprise")
@handle_errors
def clients_create(
    full_name: str,
    email: str,
    phone: str,
    company_name: str,
) -> None:
    """Créer un client (associé au commercial connecté)."""
    with session_scope() as session:
        client = create_client(
            session,
            full_name=full_name,
            email=email,
            phone=phone,
            company_name=company_name,
        )
    display.success(f"Client créé #{client.id} — {client.company_name}")


@clients_group.command("update")
@click.argument("client_id", type=int)
@click.option("--name", "full_name", default=None)
@click.option("--email", default=None)
@click.option("--phone", default=None)
@click.option("--company", "company_name", default=None)
@handle_errors
def clients_update(
    client_id: int,
    full_name: str | None,
    email: str | None,
    phone: str | None,
    company_name: str | None,
) -> None:
    """Mettre à jour un de ses clients."""
    with session_scope() as session:
        client = update_client(
            session,
            client_id,
            full_name=optional_text(full_name),
            email=optional_text(email),
            phone=optional_text(phone),
            company_name=optional_text(company_name),
        )
    display.success(f"Client #{client.id} mis à jour.")
