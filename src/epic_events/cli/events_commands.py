"""Commandes événements."""

from __future__ import annotations

import click

from epic_events.cli import display
from epic_events.cli.utils import handle_errors, optional_text, parse_datetime
from epic_events.db import session_scope
from epic_events.services.events import create_event, list_events, update_event


@click.group("events")
def events_group() -> None:
    """Gérer les événements."""


@events_group.command("list")
@click.option("--no-support", is_flag=True, help="Sans collaborateur support")
@click.option("--mine", is_flag=True, help="Uniquement mes événements (support)")
@handle_errors
def events_list(no_support: bool, mine: bool) -> None:
    """Lister les événements."""
    with session_scope() as session:
        display.render_events(
            list_events(session, without_support=no_support, mine_only=mine)
        )


@events_group.command("create")
@click.option("--contract-id", type=int, prompt="ID contrat")
@click.option("--name", prompt="Nom de l'événement")
@click.option("--start", "start_raw", prompt="Début (YYYY-MM-DD HH:MM)")
@click.option("--end", "end_raw", prompt="Fin (YYYY-MM-DD HH:MM)")
@click.option("--location", prompt="Lieu")
@click.option("--attendees", type=int, prompt="Participants")
@click.option("--notes", default=None)
@handle_errors
def events_create(
    contract_id: int,
    name: str,
    start_raw: str,
    end_raw: str,
    location: str,
    attendees: int,
    notes: str | None,
) -> None:
    """Créer un événement pour un contrat signé."""
    with session_scope() as session:
        event = create_event(
            session,
            contract_id=contract_id,
            name=name,
            start_date=parse_datetime(start_raw),
            end_date=parse_datetime(end_raw),
            location=location,
            attendees=attendees,
            notes=optional_text(notes),
        )
        event_id = event.id
    display.success(f"Événement créé #{event_id}")


@events_group.command("update")
@click.argument("event_id", type=int)
@click.option("--name", default=None)
@click.option("--start", "start_raw", default=None)
@click.option("--end", "end_raw", default=None)
@click.option("--location", default=None)
@click.option("--attendees", type=int, default=None)
@click.option("--notes", default=None)
@click.option(
    "--support-id",
    type=int,
    default=None,
    help="ID du support (0 pour retirer)",
)
@handle_errors
def events_update(
    event_id: int,
    name: str | None,
    start_raw: str | None,
    end_raw: str | None,
    location: str | None,
    attendees: int | None,
    notes: str | None,
    support_id: int | None,
) -> None:
    """Mettre à jour un événement."""
    clear_support = support_id == 0
    support_contact_id = support_id if support_id not in (None, 0) else None
    with session_scope() as session:
        event = update_event(
            session,
            event_id,
            name=optional_text(name),
            start_date=parse_datetime(start_raw) if start_raw else None,
            end_date=parse_datetime(end_raw) if end_raw else None,
            location=optional_text(location),
            attendees=attendees,
            notes=optional_text(notes),
            support_contact_id=support_contact_id,
            clear_support=clear_support,
        )
        updated_id = event.id
    display.success(f"Événement #{updated_id} mis à jour.")
