"""Lecture des contrats."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from epic_events.auth.permissions import Permission
from epic_events.auth.session import require_permission
from epic_events.models.contract import Contract


def list_contracts(session: Session) -> list[Contract]:
    """Retourne tous les contrats (lecture réservée aux utilisateurs authentifiés)."""
    require_permission(session, Permission.VIEW_CONTRACTS)
    stmt = (
        select(Contract)
        .options(
            joinedload(Contract.client),
            joinedload(Contract.sales_contact),
        )
        .order_by(Contract.id)
    )
    return list(session.scalars(stmt).unique().all())
