"""Services liés aux collaborateurs (création, identification, gestion)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from epic_events.auth.permissions import Permission, get_employee_permissions, has_permission
from epic_events.auth.session import require_permission
from epic_events.models.department import Department
from epic_events.models.employee import Employee
from epic_events.security.passwords import hash_password, verify_password


class EmployeeError(Exception):
    """Erreur métier liée aux collaborateurs."""


@dataclass(frozen=True)
class EmployeeIdentity:
    """Vue d'identification d'un collaborateur (sans le hash du mot de passe)."""

    id: int
    employee_number: str
    full_name: str
    email: str
    department: str
    permissions: frozenset[Permission]


def to_identity(employee: Employee) -> EmployeeIdentity:
    """Construit une vue d'identification à partir d'un Employee ORM."""
    return EmployeeIdentity(
        id=employee.id,
        employee_number=employee.employee_number,
        full_name=employee.full_name,
        email=employee.email,
        department=employee.department.name,
        permissions=get_employee_permissions(employee),
    )


def _get_department(session: Session, department_name: str) -> Department:
    department = session.scalar(
        select(Department).where(Department.name == department_name)
    )
    if department is None:
        raise EmployeeError(f"Département inconnu : {department_name!r}.")
    return department


def _validate_employee_fields(
    *,
    employee_number: str,
    full_name: str,
    email: str,
    password: str | None = None,
) -> tuple[str, str, str]:
    email_normalized = email.strip().lower()
    number = employee_number.strip()
    name = full_name.strip()
    if not number:
        raise EmployeeError("Le numéro d'employé est obligatoire.")
    if not name:
        raise EmployeeError("Le nom est obligatoire.")
    if "@" not in email_normalized:
        raise EmployeeError("Adresse email invalide.")
    if password is not None and len(password) < 8:
        raise EmployeeError("Le mot de passe doit contenir au moins 8 caractères.")
    return number, name, email_normalized


def create_employee(
    session: Session,
    *,
    employee_number: str,
    full_name: str,
    email: str,
    password: str,
    department_name: str,
) -> EmployeeIdentity:
    """Crée un collaborateur avec mot de passe haché (Argon2).

    Sans contrôle de permission — réservé au seed / bootstrap.
    Préférer create_collaborator pour une action métier authentifiée.
    """
    number, name, email_normalized = _validate_employee_fields(
        employee_number=employee_number,
        full_name=full_name,
        email=email,
        password=password,
    )

    existing = session.scalar(
        select(Employee).where(
            (Employee.email == email_normalized) | (Employee.employee_number == number)
        )
    )
    if existing is not None:
        raise EmployeeError(
            "Un collaborateur existe déjà avec cet email ou ce numéro d'employé."
        )

    department = _get_department(session, department_name)
    employee = Employee(
        employee_number=number,
        full_name=name,
        email=email_normalized,
        password_hash=hash_password(password),
        department_id=department.id,
        department=department,
    )
    session.add(employee)
    session.flush()
    return to_identity(employee)


def create_collaborator(
    session: Session,
    *,
    employee_number: str,
    full_name: str,
    email: str,
    password: str,
    department_name: str,
) -> EmployeeIdentity:
    """Crée un collaborateur (réservé à la gestion)."""
    require_permission(session, Permission.MANAGE_EMPLOYEES)
    return create_employee(
        session,
        employee_number=employee_number,
        full_name=full_name,
        email=email,
        password=password,
        department_name=department_name,
    )


def list_employees(session: Session) -> list[Employee]:
    """Liste tous les collaborateurs (gestion)."""
    require_permission(session, Permission.MANAGE_EMPLOYEES)
    stmt = (
        select(Employee)
        .options(joinedload(Employee.department))
        .order_by(Employee.id)
    )
    return list(session.scalars(stmt).unique().all())


def update_collaborator(
    session: Session,
    employee_id: int,
    *,
    employee_number: str | None = None,
    full_name: str | None = None,
    email: str | None = None,
    password: str | None = None,
    department_name: str | None = None,
) -> EmployeeIdentity:
    """Met à jour un collaborateur, y compris son département (gestion)."""
    actor = require_permission(session, Permission.MANAGE_EMPLOYEES)
    employee = session.scalar(
        select(Employee)
        .options(joinedload(Employee.department))
        .where(Employee.id == employee_id)
    )
    if employee is None:
        raise EmployeeError(f"Collaborateur #{employee_id} introuvable.")

    if employee_number is not None:
        number = employee_number.strip()
        if not number:
            raise EmployeeError("Le numéro d'employé est obligatoire.")
        conflict = session.scalar(
            select(Employee).where(
                Employee.employee_number == number,
                Employee.id != employee_id,
            )
        )
        if conflict is not None:
            raise EmployeeError("Ce numéro d'employé est déjà utilisé.")
        employee.employee_number = number

    if full_name is not None:
        name = full_name.strip()
        if not name:
            raise EmployeeError("Le nom est obligatoire.")
        employee.full_name = name

    if email is not None:
        email_normalized = email.strip().lower()
        if "@" not in email_normalized:
            raise EmployeeError("Adresse email invalide.")
        conflict = session.scalar(
            select(Employee).where(
                Employee.email == email_normalized,
                Employee.id != employee_id,
            )
        )
        if conflict is not None:
            raise EmployeeError("Cet email est déjà utilisé.")
        employee.email = email_normalized

    if password is not None:
        if len(password) < 8:
            raise EmployeeError("Le mot de passe doit contenir au moins 8 caractères.")
        employee.password_hash = hash_password(password)

    if department_name is not None:
        department = _get_department(session, department_name)
        employee.department = department
        employee.department_id = department.id

    # Empêche de se retirer soi-même la capacité de gérer les comptes
    if employee.id == actor.id and not has_permission(
        employee, Permission.MANAGE_EMPLOYEES
    ):
        raise EmployeeError(
            "Vous ne pouvez pas retirer votre propre accès gestion."
        )

    session.flush()
    return to_identity(employee)


def delete_collaborator(session: Session, employee_id: int) -> None:
    """Supprime un collaborateur (gestion)."""
    actor = require_permission(session, Permission.MANAGE_EMPLOYEES)
    if actor.id == employee_id:
        raise EmployeeError("Vous ne pouvez pas supprimer votre propre compte.")

    employee = session.get(Employee, employee_id)
    if employee is None:
        raise EmployeeError(f"Collaborateur #{employee_id} introuvable.")
    session.delete(employee)
    session.flush()


def get_employee_by_email(session: Session, email: str) -> Employee | None:
    """Charge un collaborateur et son département par email."""
    return session.scalar(
        select(Employee)
        .options(joinedload(Employee.department))
        .where(Employee.email == email.strip().lower())
    )


def get_employee_by_number(session: Session, employee_number: str) -> Employee | None:
    """Charge un collaborateur et son département par numéro d'employé."""
    return session.scalar(
        select(Employee)
        .options(joinedload(Employee.department))
        .where(Employee.employee_number == employee_number.strip())
    )


def identify_employee(
    session: Session,
    *,
    email: str,
    password: str,
) -> EmployeeIdentity | None:
    """Vérifie email + mot de passe et retourne l'identité, ou None si échec.

    Ne révèle pas si l'échec vient de l'email ou du mot de passe
    (évite l'énumération de comptes).
    """
    employee = get_employee_by_email(session, email)
    if employee is None:
        return None
    if not verify_password(employee.password_hash, password):
        return None
    return to_identity(employee)
