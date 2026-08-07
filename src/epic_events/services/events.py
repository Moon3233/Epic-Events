"""Lecture des événements."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from epic_events.auth.permissions import Permission
from epic_events.auth.session import require_permission
from epic_events.models.contract import Contract
from epic_events.models.event import Event


def list_events(session: Session) -> list[Event]:
    """Retourne tous les événements (lecture réservée aux utilisateurs authentifiés)."""
    require_permission(session, Permission.VIEW_EVENTS)
    stmt = (
        select(Event)
        .options(
            joinedload(Event.support_contact),
            joinedload(Event.contract).joinedload(Contract.client),
        )
        .order_by(Event.id)
    )
    return list(session.scalars(stmt).unique().all())
