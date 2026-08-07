"""Services liés aux collaborateurs (création et identification)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from epic_events.auth.permissions import Permission, get_employee_permissions
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


def create_employee(
    session: Session,
    *,
    employee_number: str,
    full_name: str,
    email: str,
    password: str,
    department_name: str,
) -> EmployeeIdentity:
    """Crée un collaborateur avec mot de passe haché (Argon2)."""
    email_normalized = email.strip().lower()
    if not employee_number.strip():
        raise EmployeeError("Le numéro d'employé est obligatoire.")
    if not full_name.strip():
        raise EmployeeError("Le nom est obligatoire.")
    if "@" not in email_normalized:
        raise EmployeeError("Adresse email invalide.")
    if len(password) < 8:
        raise EmployeeError("Le mot de passe doit contenir au moins 8 caractères.")

    existing = session.scalar(
        select(Employee).where(
            (Employee.email == email_normalized)
            | (Employee.employee_number == employee_number.strip())
        )
    )
    if existing is not None:
        raise EmployeeError(
            "Un collaborateur existe déjà avec cet email ou ce numéro d'employé."
        )

    department = _get_department(session, department_name)
    employee = Employee(
        employee_number=employee_number.strip(),
        full_name=full_name.strip(),
        email=email_normalized,
        password_hash=hash_password(password),
        department_id=department.id,
        department=department,
    )
    session.add(employee)
    session.flush()
    return to_identity(employee)


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
