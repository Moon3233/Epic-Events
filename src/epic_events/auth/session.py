"""Authentification persistante et contrôle d'autorisation."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from epic_events.auth.permissions import Permission, has_permission
from epic_events.auth.session_store import clear_token, load_token, save_token
from epic_events.auth.tokens import TokenError, create_access_token, decode_access_token
from epic_events.models.employee import Employee
from epic_events.services.employees import (
    EmployeeIdentity,
    identify_employee,
    to_identity,
)


class AuthenticationError(Exception):
    """Échec d'authentification ou session absente / invalide."""


class AuthorizationError(Exception):
    """L'utilisateur authentifié n'a pas la permission requise."""


def login(session: Session, *, email: str, password: str) -> EmployeeIdentity:
    """Authentifie, émet un JWT et le stocke localement."""
    identity = identify_employee(session, email=email, password=password)
    if identity is None:
        raise AuthenticationError("Email ou mot de passe incorrect.")

    token = create_access_token(
        employee_id=identity.id,
        email=identity.email,
        department=identity.department,
    )
    save_token(token)
    return identity


def logout() -> None:
    """Supprime le jeton local."""
    clear_token()


def get_current_employee(session: Session) -> Employee:
    """Charge l'employé courant depuis le JWT + la base.

    Les permissions sont toujours relues en BDD (pas figées dans le jeton).
    """
    token = load_token()
    if token is None:
        raise AuthenticationError(
            "Aucune session active. Connectez-vous avec la commande login."
        )

    try:
        payload = decode_access_token(token)
    except TokenError as exc:
        clear_token()
        raise AuthenticationError(str(exc)) from exc

    try:
        employee_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        clear_token()
        raise AuthenticationError("Jeton invalide. Reconnectez-vous.") from exc

    employee = session.scalar(
        select(Employee)
        .options(joinedload(Employee.department))
        .where(Employee.id == employee_id)
    )
    if employee is None:
        clear_token()
        raise AuthenticationError(
            "Compte introuvable. Reconnectez-vous."
        )
    return employee


def get_current_identity(session: Session) -> EmployeeIdentity:
    """Retourne l'identité (avec permissions) de la session courante."""
    return to_identity(get_current_employee(session))


def require_permission(session: Session, permission: Permission) -> Employee:
    """Vérifie authentification + autorisation ; retourne l'employé courant."""
    employee = get_current_employee(session)
    if not has_permission(employee, permission):
        raise AuthorizationError(
            f"Permission refusée : {permission.value} "
            f"(département « {employee.department.name} »)."
        )
    return employee
