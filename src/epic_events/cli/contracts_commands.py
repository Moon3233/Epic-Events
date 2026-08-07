"""Commandes contrats."""

from __future__ import annotations

from decimal import Decimal

import click

from epic_events.cli import display
from epic_events.cli.utils import handle_errors, optional_text
from epic_events.db import session_scope
from epic_events.services.contracts import create_contract, list_contracts, update_contract


@click.group("contracts")
def contracts_group() -> None:
    """Gérer les contrats."""


@contracts_group.command("list")
@click.option("--unsigned", is_flag=True, help="Uniquement non signés")
@click.option("--unpaid", is_flag=True, help="Reste à payer > 0")
@handle_errors
def contracts_list(unsigned: bool, unpaid: bool) -> None:
    """Lister les contrats."""
    with session_scope() as session:
        display.render_contracts(
            list_contracts(session, unsigned_only=unsigned, unpaid_only=unpaid)
        )


@contracts_group.command("create")
@click.option("--client-id", type=int, prompt="ID client")
@click.option("--total", "total_amount", prompt="Montant total")
@click.option("--remaining", "remaining_amount", default=None, prompt="Reste à payer")
@click.option("--signed/--unsigned", default=False, show_default=True)
@click.option("--sales-contact-id", type=int, default=None)
@handle_errors
def contracts_create(
    client_id: int,
    total_amount: str,
    remaining_amount: str | None,
    signed: bool,
    sales_contact_id: int | None,
) -> None:
    """Créer un contrat (gestion)."""
    with session_scope() as session:
        contract = create_contract(
            session,
            client_id=client_id,
            total_amount=total_amount,
            remaining_amount=optional_text(remaining_amount),
            is_signed=signed,
            sales_contact_id=sales_contact_id,
        )
    display.success(f"Contrat créé #{contract.id}")


@contracts_group.command("update")
@click.argument("contract_id", type=int)
@click.option("--client-id", type=int, default=None)
@click.option("--sales-contact-id", type=int, default=None)
@click.option("--total", "total_amount", default=None)
@click.option("--remaining", "remaining_amount", default=None)
@click.option("--signed/--unsigned", default=None)
@handle_errors
def contracts_update(
    contract_id: int,
    client_id: int | None,
    sales_contact_id: int | None,
    total_amount: str | None,
    remaining_amount: str | None,
    signed: bool | None,
) -> None:
    """Mettre à jour un contrat."""
    with session_scope() as session:
        contract = update_contract(
            session,
            contract_id,
            client_id=client_id,
            sales_contact_id=sales_contact_id,
            total_amount=Decimal(total_amount) if total_amount else None,
            remaining_amount=Decimal(remaining_amount) if remaining_amount else None,
            is_signed=signed,
        )
    display.success(f"Contrat #{contract.id} mis à jour.")
