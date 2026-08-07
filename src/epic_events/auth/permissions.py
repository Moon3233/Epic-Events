"""Permissions métier dérivées du département (autorisation).

Authentification = qui es-tu ? (identité vérifiée)
Autorisation    = que peux-tu faire ? (permissions ci-dessous)
"""

from __future__ import annotations

from enum import Enum, unique

from epic_events.models.employee import Employee


@unique
class Permission(str, Enum):
    """Actions autorisées dans le CRM."""

    # Lecture (tous les départements)
    VIEW_CLIENTS = "view_clients"
    VIEW_CONTRACTS = "view_contracts"
    VIEW_EVENTS = "view_events"

    # Gestion
    MANAGE_EMPLOYEES = "manage_employees"
    CREATE_CONTRACT = "create_contract"
    UPDATE_ANY_CONTRACT = "update_any_contract"
    UPDATE_ANY_EVENT = "update_any_event"
    FILTER_EVENTS_WITHOUT_SUPPORT = "filter_events_without_support"

    # Commercial
    CREATE_CLIENT = "create_client"
    UPDATE_OWN_CLIENT = "update_own_client"
    UPDATE_OWN_CONTRACT = "update_own_contract"
    FILTER_CONTRACTS = "filter_contracts"
    CREATE_EVENT = "create_event"

    # Support
    FILTER_OWN_EVENTS = "filter_own_events"
    UPDATE_OWN_EVENT = "update_own_event"


# Lecture commune à tous les collaborateurs authentifiés
_READ_ALL = frozenset(
    {
        Permission.VIEW_CLIENTS,
        Permission.VIEW_CONTRACTS,
        Permission.VIEW_EVENTS,
    }
)

DEPARTMENT_PERMISSIONS: dict[str, frozenset[Permission]] = {
    "gestion": _READ_ALL
    | frozenset(
        {
            Permission.MANAGE_EMPLOYEES,
            Permission.CREATE_CONTRACT,
            Permission.UPDATE_ANY_CONTRACT,
            Permission.UPDATE_ANY_EVENT,
            Permission.FILTER_EVENTS_WITHOUT_SUPPORT,
            Permission.FILTER_CONTRACTS,
        }
    ),
    "commercial": _READ_ALL
    | frozenset(
        {
            Permission.CREATE_CLIENT,
            Permission.UPDATE_OWN_CLIENT,
            Permission.UPDATE_OWN_CONTRACT,
            Permission.FILTER_CONTRACTS,
            Permission.CREATE_EVENT,
        }
    ),
    "support": _READ_ALL
    | frozenset(
        {
            Permission.FILTER_OWN_EVENTS,
            Permission.UPDATE_OWN_EVENT,
        }
    ),
}


def permissions_for_department(department_name: str) -> frozenset[Permission]:
    """Retourne les permissions d'un département, ou un ensemble vide si inconnu."""
    return DEPARTMENT_PERMISSIONS.get(department_name, frozenset())


def get_employee_permissions(employee: Employee) -> frozenset[Permission]:
    """Dérive les permissions via la relation Employee → Department."""
    return permissions_for_department(employee.department.name)


def has_permission(employee: Employee, permission: Permission) -> bool:
    """Vérifie si le collaborateur possède une permission donnée."""
    return permission in get_employee_permissions(employee)
