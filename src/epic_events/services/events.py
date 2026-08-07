"""Services événements (lecture, création, mise à jour, filtres)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from epic_events.auth.permissions import Permission, has_permission
from epic_events.auth.session import AuthorizationError, require_any_permission, require_permission
from epic_events.models.contract import Contract
from epic_events.models.employee import Employee
from epic_events.models.event import Event


class EventError(Exception):
    """Erreur métier liée aux événements."""


def list_events(
    session: Session,
    *,
    without_support: bool = False,
    mine_only: bool = False,
) -> list[Event]:
    """Liste les événements, avec filtres optionnels selon le rôle."""
    actor = require_permission(session, Permission.VIEW_EVENTS)

    if without_support and not has_permission(
        actor, Permission.FILTER_EVENTS_WITHOUT_SUPPORT
    ):
        raise AuthorizationError(
            "Permission refusée : filter_events_without_support "
            f"(département « {actor.department.name} »)."
        )
    if mine_only and not has_permission(actor, Permission.FILTER_OWN_EVENTS):
        raise AuthorizationError(
            "Permission refusée : filter_own_events "
            f"(département « {actor.department.name} »)."
        )

    stmt = (
        select(Event)
        .options(
            joinedload(Event.support_contact),
            joinedload(Event.contract).joinedload(Contract.client),
        )
        .order_by(Event.id)
    )
    if without_support:
        stmt = stmt.where(Event.support_contact_id.is_(None))
    if mine_only:
        stmt = stmt.where(Event.support_contact_id == actor.id)

    return list(session.scalars(stmt).unique().all())


def create_event(
    session: Session,
    *,
    contract_id: int,
    name: str,
    start_date: datetime,
    end_date: datetime,
    location: str,
    attendees: int,
    notes: str | None = None,
) -> Event:
    """Crée un événement pour un contrat signé du commercial connecté."""
    actor = require_permission(session, Permission.CREATE_EVENT)

    contract = session.scalar(
        select(Contract)
        .options(joinedload(Contract.client))
        .where(Contract.id == contract_id)
    )
    if contract is None:
        raise EventError(f"Contrat #{contract_id} introuvable.")
    if contract.sales_contact_id != actor.id:
        raise EventError("Vous ne pouvez créer un événement que pour vos contrats.")
    if not contract.is_signed:
        raise EventError("Le contrat doit être signé avant de créer un événement.")

    existing = session.scalar(select(Event).where(Event.contract_id == contract_id))
    if existing is not None:
        raise EventError("Un événement existe déjà pour ce contrat.")

    event_name = name.strip()
    place = location.strip()
    if not event_name or not place:
        raise EventError("Le nom et le lieu sont obligatoires.")
    if end_date < start_date:
        raise EventError("La date de fin doit être postérieure au début.")
    if attendees < 1:
        raise EventError("Le nombre de participants doit être au moins 1.")

    event = Event(
        name=event_name,
        contract_id=contract.id,
        start_date=start_date,
        end_date=end_date,
        location=place,
        attendees=attendees,
        notes=notes.strip() if notes else None,
        support_contact_id=None,
    )
    session.add(event)
    session.flush()
    return event


def update_event(
    session: Session,
    event_id: int,
    *,
    name: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    location: str | None = None,
    attendees: int | None = None,
    notes: str | None = None,
    support_contact_id: int | None = None,
    clear_support: bool = False,
) -> Event:
    """Met à jour un événement (gestion : tous ; support : les siens)."""
    actor = require_any_permission(
        session,
        Permission.UPDATE_ANY_EVENT,
        Permission.UPDATE_OWN_EVENT,
    )

    event = session.scalar(
        select(Event)
        .options(
            joinedload(Event.support_contact),
            joinedload(Event.contract).joinedload(Contract.client),
        )
        .where(Event.id == event_id)
    )
    if event is None:
        raise EventError(f"Événement #{event_id} introuvable.")

    can_update_any = has_permission(actor, Permission.UPDATE_ANY_EVENT)
    if not can_update_any and event.support_contact_id != actor.id:
        raise EventError("Vous ne pouvez modifier que vos propres événements.")

    if name is not None:
        event_name = name.strip()
        if not event_name:
            raise EventError("Le nom est obligatoire.")
        event.name = event_name
    if location is not None:
        place = location.strip()
        if not place:
            raise EventError("Le lieu est obligatoire.")
        event.location = place
    if start_date is not None:
        event.start_date = start_date
    if end_date is not None:
        event.end_date = end_date
    if event.end_date < event.start_date:
        raise EventError("La date de fin doit être postérieure au début.")
    if attendees is not None:
        if attendees < 1:
            raise EventError("Le nombre de participants doit être au moins 1.")
        event.attendees = attendees
    if notes is not None:
        event.notes = notes.strip() or None

    if clear_support:
        if not can_update_any:
            raise EventError("Seul le département gestion peut retirer le support.")
        event.support_contact_id = None
    elif support_contact_id is not None:
        if not can_update_any:
            raise EventError(
                "Seul le département gestion peut assigner un support."
            )
        support = session.get(Employee, support_contact_id)
        if support is None:
            raise EventError(f"Collaborateur support #{support_contact_id} introuvable.")
        event.support_contact_id = support_contact_id

    session.flush()
    return event
