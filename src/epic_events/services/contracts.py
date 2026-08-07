"""Services contrats (lecture, création, mise à jour, filtres)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from epic_events.auth.permissions import Permission, has_permission
from epic_events.auth.session import require_any_permission, require_permission
from epic_events.models.client import Client
from epic_events.models.contract import Contract
from epic_events.models.employee import Employee


class ContractError(Exception):
    """Erreur métier liée aux contrats."""


def _parse_amount(value: str | Decimal) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ContractError("Montant invalide.") from exc
    if amount < 0:
        raise ContractError("Un montant ne peut pas être négatif.")
    return amount.quantize(Decimal("0.01"))


def list_contracts(
    session: Session,
    *,
    unsigned_only: bool = False,
    unpaid_only: bool = False,
) -> list[Contract]:
    """Liste les contrats, avec filtres optionnels (commercial)."""
    actor = require_permission(session, Permission.VIEW_CONTRACTS)

    if unsigned_only or unpaid_only:
        if not has_permission(actor, Permission.FILTER_CONTRACTS):
            from epic_events.auth.session import AuthorizationError

            raise AuthorizationError(
                "Permission refusée : filter_contracts "
                f"(département « {actor.department.name} »)."
            )

    stmt = (
        select(Contract)
        .options(
            joinedload(Contract.client),
            joinedload(Contract.sales_contact),
        )
        .order_by(Contract.id)
    )
    if unsigned_only:
        stmt = stmt.where(Contract.is_signed.is_(False))
    if unpaid_only:
        stmt = stmt.where(Contract.remaining_amount > 0)

    return list(session.scalars(stmt).unique().all())


def create_contract(
    session: Session,
    *,
    client_id: int,
    total_amount: str | Decimal,
    remaining_amount: str | Decimal | None = None,
    is_signed: bool = False,
    sales_contact_id: int | None = None,
) -> Contract:
    """Crée un contrat (gestion) lié à un client."""
    require_permission(session, Permission.CREATE_CONTRACT)

    client = session.scalar(
        select(Client).where(Client.id == client_id)
    )
    if client is None:
        raise ContractError(f"Client #{client_id} introuvable.")

    total = _parse_amount(total_amount)
    remaining = (
        total if remaining_amount is None else _parse_amount(remaining_amount)
    )
    if remaining > total:
        raise ContractError("Le reste à payer ne peut pas dépasser le total.")

    contact_id = sales_contact_id or client.sales_contact_id
    contact = session.get(Employee, contact_id)
    if contact is None:
        raise ContractError(f"Commercial #{contact_id} introuvable.")

    contract = Contract(
        client_id=client.id,
        sales_contact_id=contact_id,
        total_amount=total,
        remaining_amount=remaining,
        is_signed=is_signed,
    )
    session.add(contract)
    session.flush()
    session.refresh(contract, attribute_names=["client", "sales_contact"])

    if is_signed:
        from epic_events.logging_sentry import log_event

        log_event(
            "Contrat signé",
            contract_id=contract.id,
            client_id=contract.client_id,
            sales_contact_id=contract.sales_contact_id,
        )

    return contract


def update_contract(
    session: Session,
    contract_id: int,
    *,
    client_id: int | None = None,
    sales_contact_id: int | None = None,
    total_amount: str | Decimal | None = None,
    remaining_amount: str | Decimal | None = None,
    is_signed: bool | None = None,
) -> Contract:
    """Met à jour un contrat (gestion : tous ; commercial : les siens)."""
    actor = require_any_permission(
        session,
        Permission.UPDATE_ANY_CONTRACT,
        Permission.UPDATE_OWN_CONTRACT,
    )

    contract = session.scalar(
        select(Contract)
        .options(
            joinedload(Contract.client),
            joinedload(Contract.sales_contact),
        )
        .where(Contract.id == contract_id)
    )
    if contract is None:
        raise ContractError(f"Contrat #{contract_id} introuvable.")

    can_update_any = has_permission(actor, Permission.UPDATE_ANY_CONTRACT)
    if not can_update_any and contract.sales_contact_id != actor.id:
        raise ContractError("Vous ne pouvez modifier que vos propres contrats.")

    if client_id is not None:
        if not can_update_any:
            raise ContractError(
                "Seul le département gestion peut changer le client d'un contrat."
            )
        client = session.get(Client, client_id)
        if client is None:
            raise ContractError(f"Client #{client_id} introuvable.")
        contract.client_id = client_id

    if sales_contact_id is not None:
        if not can_update_any:
            raise ContractError(
                "Seul le département gestion peut changer le commercial du contrat."
            )
        contact = session.get(Employee, sales_contact_id)
        if contact is None:
            raise ContractError(f"Commercial #{sales_contact_id} introuvable.")
        contract.sales_contact_id = sales_contact_id

    if total_amount is not None:
        contract.total_amount = _parse_amount(total_amount)
    if remaining_amount is not None:
        contract.remaining_amount = _parse_amount(remaining_amount)
    if contract.remaining_amount > contract.total_amount:
        raise ContractError("Le reste à payer ne peut pas dépasser le total.")

    if is_signed is not None:
        was_signed = contract.is_signed
        contract.is_signed = is_signed
        if is_signed and not was_signed:
            from epic_events.logging_sentry import log_event

            log_event(
                "Contrat signé",
                contract_id=contract.id,
                client_id=contract.client_id,
                sales_contact_id=contract.sales_contact_id,
                actor_id=actor.id,
            )

    session.flush()
    return contract
