"""Services clients (lecture, création, mise à jour)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from epic_events.auth.permissions import Permission
from epic_events.auth.session import require_permission
from epic_events.models.client import Client


class ClientError(Exception):
    """Erreur métier liée aux clients."""


def list_clients(session: Session) -> list[Client]:
    """Retourne tous les clients (lecture authentifiée)."""
    require_permission(session, Permission.VIEW_CLIENTS)
    stmt = (
        select(Client)
        .options(joinedload(Client.sales_contact))
        .order_by(Client.id)
    )
    return list(session.scalars(stmt).unique().all())


def create_client(
    session: Session,
    *,
    full_name: str,
    email: str,
    phone: str,
    company_name: str,
) -> Client:
    """Crée un client associé automatiquement au commercial connecté."""
    actor = require_permission(session, Permission.CREATE_CLIENT)

    name = full_name.strip()
    email_normalized = email.strip().lower()
    phone_value = phone.strip()
    company = company_name.strip()
    if not name or not phone_value or not company:
        raise ClientError("Nom, téléphone et entreprise sont obligatoires.")
    if "@" not in email_normalized:
        raise ClientError("Adresse email invalide.")

    client = Client(
        full_name=name,
        email=email_normalized,
        phone=phone_value,
        company_name=company,
        sales_contact_id=actor.id,
    )
    session.add(client)
    session.flush()
    session.refresh(client, attribute_names=["sales_contact"])
    return client


def update_client(
    session: Session,
    client_id: int,
    *,
    full_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    company_name: str | None = None,
) -> Client:
    """Met à jour un client dont le commercial connecté est responsable."""
    actor = require_permission(session, Permission.UPDATE_OWN_CLIENT)
    client = session.scalar(
        select(Client)
        .options(joinedload(Client.sales_contact))
        .where(Client.id == client_id)
    )
    if client is None:
        raise ClientError(f"Client #{client_id} introuvable.")
    if client.sales_contact_id != actor.id:
        raise ClientError("Vous ne pouvez modifier que vos propres clients.")

    if full_name is not None:
        name = full_name.strip()
        if not name:
            raise ClientError("Le nom est obligatoire.")
        client.full_name = name
    if email is not None:
        email_normalized = email.strip().lower()
        if "@" not in email_normalized:
            raise ClientError("Adresse email invalide.")
        client.email = email_normalized
    if phone is not None:
        phone_value = phone.strip()
        if not phone_value:
            raise ClientError("Le téléphone est obligatoire.")
        client.phone = phone_value
    if company_name is not None:
        company = company_name.strip()
        if not company:
            raise ClientError("L'entreprise est obligatoire.")
        client.company_name = company

    client.updated_at = datetime.now(UTC)
    session.flush()
    return client
