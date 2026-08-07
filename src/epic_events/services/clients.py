"""Lecture des clients."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from epic_events.auth.permissions import Permission
from epic_events.auth.session import require_permission
from epic_events.models.client import Client


def list_clients(session: Session) -> list[Client]:
    """Retourne tous les clients (lecture réservée aux utilisateurs authentifiés)."""
    require_permission(session, Permission.VIEW_CLIENTS)
    stmt = (
        select(Client)
        .options(joinedload(Client.sales_contact))
        .order_by(Client.id)
    )
    return list(session.scalars(stmt).unique().all())
