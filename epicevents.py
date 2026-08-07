#!/usr/bin/env python3
"""Point d'entrée CLI Epic Events."""

from __future__ import annotations

import argparse
import getpass
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from epic_events.auth.session import (  # noqa: E402
    AuthenticationError,
    AuthorizationError,
    get_current_identity,
    login,
    logout,
)
from epic_events.cli.utils import (  # noqa: E402
    parse_datetime,
    print_error,
    prompt,
    prompt_optional,
)
from epic_events.db import session_scope  # noqa: E402
from epic_events.services.clients import (  # noqa: E402
    ClientError,
    create_client,
    list_clients,
    update_client,
)
from epic_events.services.contracts import (  # noqa: E402
    ContractError,
    create_contract,
    list_contracts,
    update_contract,
)
from epic_events.services.employees import (  # noqa: E402
    EmployeeError,
    create_collaborator,
    delete_collaborator,
    list_employees,
    update_collaborator,
)
from epic_events.services.events import (  # noqa: E402
    EventError,
    create_event,
    list_events,
    update_event,
)

ServiceError = (
    AuthenticationError,
    AuthorizationError,
    EmployeeError,
    ClientError,
    ContractError,
    EventError,
    ValueError,
)


def cmd_login(_: argparse.Namespace) -> int:
    email = input("Email : ").strip()
    password = getpass.getpass("Mot de passe : ")
    try:
        with session_scope() as session:
            identity = login(session, email=email, password=password)
    except ServiceError as exc:
        print_error(exc)
        return 1
    print(f"Connecté : {identity.full_name} ({identity.department})")
    return 0


def cmd_logout(_: argparse.Namespace) -> int:
    logout()
    print("Déconnecté.")
    return 0


def cmd_whoami(_: argparse.Namespace) -> int:
    try:
        with session_scope() as session:
            identity = get_current_identity(session)
    except ServiceError as exc:
        print_error(exc)
        return 1
    perms = ", ".join(sorted(p.value for p in identity.permissions))
    print(f"Nom      : {identity.full_name}")
    print(f"Email    : {identity.email}")
    print(f"N°       : {identity.employee_number}")
    print(f"Dépt.    : {identity.department}")
    print(f"Droits   : {perms}")
    return 0


def cmd_clients_list(_: argparse.Namespace) -> int:
    try:
        with session_scope() as session:
            clients = list_clients(session)
            rows = [
                (
                    c.id,
                    c.full_name,
                    c.company_name,
                    c.email,
                    c.sales_contact.full_name,
                )
                for c in clients
            ]
    except ServiceError as exc:
        print_error(exc)
        return 1
    if not rows:
        print("Aucun client.")
        return 0
    print(f"{'ID':<4} {'Nom':<22} {'Entreprise':<22} {'Email':<28} Commercial")
    print("-" * 100)
    for row in rows:
        print(f"{row[0]:<4} {row[1]:<22} {row[2]:<22} {row[3]:<28} {row[4]}")
    return 0


def cmd_clients_create(_: argparse.Namespace) -> int:
    try:
        with session_scope() as session:
            client = create_client(
                session,
                full_name=prompt("Nom complet"),
                email=prompt("Email"),
                phone=prompt("Téléphone"),
                company_name=prompt("Entreprise"),
            )
            print(f"Client créé #{client.id} — {client.company_name}")
    except ServiceError as exc:
        print_error(exc)
        return 1
    return 0


def cmd_clients_update(args: argparse.Namespace) -> int:
    try:
        with session_scope() as session:
            client = update_client(
                session,
                args.id,
                full_name=prompt_optional("Nom complet"),
                email=prompt_optional("Email"),
                phone=prompt_optional("Téléphone"),
                company_name=prompt_optional("Entreprise"),
            )
            print(f"Client #{client.id} mis à jour.")
    except ServiceError as exc:
        print_error(exc)
        return 1
    return 0


def cmd_contracts_list(args: argparse.Namespace) -> int:
    try:
        with session_scope() as session:
            contracts = list_contracts(
                session,
                unsigned_only=args.unsigned,
                unpaid_only=args.unpaid,
            )
            rows = [
                (
                    c.id,
                    c.client.company_name,
                    c.sales_contact.full_name,
                    c.total_amount,
                    c.remaining_amount,
                    "signé" if c.is_signed else "non signé",
                )
                for c in contracts
            ]
    except ServiceError as exc:
        print_error(exc)
        return 1
    if not rows:
        print("Aucun contrat.")
        return 0
    print(
        f"{'ID':<4} {'Client':<24} {'Commercial':<20} "
        f"{'Total':>10} {'Reste':>10} Statut"
    )
    print("-" * 90)
    for row in rows:
        print(
            f"{row[0]:<4} {row[1]:<24} {row[2]:<20} "
            f"{row[3]:>10} {row[4]:>10} {row[5]}"
        )
    return 0


def cmd_contracts_create(_: argparse.Namespace) -> int:
    try:
        with session_scope() as session:
            signed_raw = prompt("Signé ? (o/n)", "n").lower()
            contract = create_contract(
                session,
                client_id=int(prompt("ID client")),
                total_amount=prompt("Montant total"),
                remaining_amount=prompt("Reste à payer") or None,
                is_signed=signed_raw in {"o", "oui", "y", "yes"},
            )
            print(f"Contrat créé #{contract.id}")
    except ServiceError as exc:
        print_error(exc)
        return 1
    return 0


def cmd_contracts_update(args: argparse.Namespace) -> int:
    try:
        with session_scope() as session:
            remaining = prompt_optional("Reste à payer")
            total = prompt_optional("Montant total")
            signed_raw = prompt_optional("Signé ? (o/n)")
            is_signed = None
            if signed_raw is not None:
                is_signed = signed_raw.lower() in {"o", "oui", "y", "yes"}
            contract = update_contract(
                session,
                args.id,
                total_amount=Decimal(total) if total else None,
                remaining_amount=Decimal(remaining) if remaining else None,
                is_signed=is_signed,
            )
            print(f"Contrat #{contract.id} mis à jour.")
    except ServiceError as exc:
        print_error(exc)
        return 1
    return 0


def cmd_events_list(args: argparse.Namespace) -> int:
    try:
        with session_scope() as session:
            events = list_events(
                session,
                without_support=args.no_support,
                mine_only=args.mine,
            )
            rows = [
                (
                    e.id,
                    e.name,
                    e.contract.client.company_name,
                    e.start_date.strftime("%Y-%m-%d %H:%M"),
                    e.support_contact.full_name if e.support_contact else "—",
                )
                for e in events
            ]
    except ServiceError as exc:
        print_error(exc)
        return 1
    if not rows:
        print("Aucun événement.")
        return 0
    print(f"{'ID':<4} {'Nom':<30} {'Client':<22} {'Début':<16} Support")
    print("-" * 100)
    for row in rows:
        print(f"{row[0]:<4} {row[1]:<30} {row[2]:<22} {row[3]:<16} {row[4]}")
    return 0


def cmd_events_create(_: argparse.Namespace) -> int:
    try:
        with session_scope() as session:
            event = create_event(
                session,
                contract_id=int(prompt("ID contrat")),
                name=prompt("Nom de l'événement"),
                start_date=parse_datetime(prompt("Début (YYYY-MM-DD HH:MM)")),
                end_date=parse_datetime(prompt("Fin (YYYY-MM-DD HH:MM)")),
                location=prompt("Lieu"),
                attendees=int(prompt("Participants")),
                notes=prompt_optional("Notes"),
            )
            print(f"Événement créé #{event.id}")
    except ServiceError as exc:
        print_error(exc)
        return 1
    return 0


def cmd_events_update(args: argparse.Namespace) -> int:
    try:
        with session_scope() as session:
            start_raw = prompt_optional("Début (YYYY-MM-DD HH:MM)")
            end_raw = prompt_optional("Fin (YYYY-MM-DD HH:MM)")
            attendees_raw = prompt_optional("Participants")
            support_raw = prompt_optional("ID support (vide=inchangé, 0=retirer)")
            clear_support = support_raw == "0"
            support_id = (
                int(support_raw)
                if support_raw not in (None, "0")
                else None
            )
            event = update_event(
                session,
                args.id,
                name=prompt_optional("Nom"),
                start_date=parse_datetime(start_raw) if start_raw else None,
                end_date=parse_datetime(end_raw) if end_raw else None,
                location=prompt_optional("Lieu"),
                attendees=int(attendees_raw) if attendees_raw else None,
                notes=prompt_optional("Notes"),
                support_contact_id=support_id,
                clear_support=clear_support,
            )
            print(f"Événement #{event.id} mis à jour.")
    except ServiceError as exc:
        print_error(exc)
        return 1
    return 0


def cmd_employees_list(_: argparse.Namespace) -> int:
    try:
        with session_scope() as session:
            employees = list_employees(session)
            rows = [
                (e.id, e.employee_number, e.full_name, e.email, e.department.name)
                for e in employees
            ]
    except ServiceError as exc:
        print_error(exc)
        return 1
    if not rows:
        print("Aucun collaborateur.")
        return 0
    print(f"{'ID':<4} {'N°':<8} {'Nom':<22} {'Email':<30} Dépt.")
    print("-" * 90)
    for row in rows:
        print(f"{row[0]:<4} {row[1]:<8} {row[2]:<22} {row[3]:<30} {row[4]}")
    return 0


def cmd_employees_create(_: argparse.Namespace) -> int:
    try:
        with session_scope() as session:
            password = getpass.getpass("Mot de passe : ")
            identity = create_collaborator(
                session,
                employee_number=prompt("N° employé"),
                full_name=prompt("Nom complet"),
                email=prompt("Email"),
                password=password,
                department_name=prompt("Département (gestion/commercial/support)"),
            )
            print(f"Collaborateur créé #{identity.id} — {identity.full_name}")
    except ServiceError as exc:
        print_error(exc)
        return 1
    return 0


def cmd_employees_update(args: argparse.Namespace) -> int:
    try:
        with session_scope() as session:
            password = prompt_optional("Nouveau mot de passe")
            identity = update_collaborator(
                session,
                args.id,
                employee_number=prompt_optional("N° employé"),
                full_name=prompt_optional("Nom complet"),
                email=prompt_optional("Email"),
                password=password,
                department_name=prompt_optional("Département"),
            )
            print(f"Collaborateur #{identity.id} mis à jour.")
    except ServiceError as exc:
        print_error(exc)
        return 1
    return 0


def cmd_employees_delete(args: argparse.Namespace) -> int:
    confirm = prompt(f"Confirmer suppression #{args.id} ? (o/n)", "n")
    if confirm.lower() not in {"o", "oui", "y", "yes"}:
        print("Annulé.")
        return 0
    try:
        with session_scope() as session:
            delete_collaborator(session, args.id)
            print(f"Collaborateur #{args.id} supprimé.")
    except ServiceError as exc:
        print_error(exc)
        return 1
    return 0


def _add_id_parser(sub, name, help_text, handler):
    parser = sub.add_parser(name, help=help_text)
    parser.add_argument("id", type=int)
    parser.set_defaults(func=handler)
    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="epicevents", description="CRM Epic Events")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, help_text, handler in (
        ("login", "S'authentifier", cmd_login),
        ("logout", "Se déconnecter", cmd_logout),
        ("whoami", "Session courante", cmd_whoami),
    ):
        p = sub.add_parser(name, help=help_text)
        p.set_defaults(func=handler)

    # clients
    clients = sub.add_parser("clients", help="Clients")
    clients_sub = clients.add_subparsers(dest="clients_cmd", required=True)
    clients_sub.add_parser("list", help="Lister").set_defaults(func=cmd_clients_list)
    clients_sub.add_parser("create", help="Créer").set_defaults(func=cmd_clients_create)
    _add_id_parser(clients_sub, "update", "Mettre à jour", cmd_clients_update)

    # contracts
    contracts = sub.add_parser("contracts", help="Contrats")
    contracts_sub = contracts.add_subparsers(dest="contracts_cmd", required=True)
    list_c = contracts_sub.add_parser("list", help="Lister")
    list_c.add_argument("--unsigned", action="store_true", help="Non signés")
    list_c.add_argument("--unpaid", action="store_true", help="Reste à payer > 0")
    list_c.set_defaults(func=cmd_contracts_list)
    contracts_sub.add_parser("create", help="Créer").set_defaults(
        func=cmd_contracts_create
    )
    _add_id_parser(contracts_sub, "update", "Mettre à jour", cmd_contracts_update)

    # events
    events = sub.add_parser("events", help="Événements")
    events_sub = events.add_subparsers(dest="events_cmd", required=True)
    list_e = events_sub.add_parser("list", help="Lister")
    list_e.add_argument("--no-support", action="store_true", help="Sans support")
    list_e.add_argument("--mine", action="store_true", help="Mes événements (support)")
    list_e.set_defaults(func=cmd_events_list)
    events_sub.add_parser("create", help="Créer").set_defaults(func=cmd_events_create)
    _add_id_parser(events_sub, "update", "Mettre à jour", cmd_events_update)

    # employees
    employees = sub.add_parser("employees", help="Collaborateurs (gestion)")
    employees_sub = employees.add_subparsers(dest="employees_cmd", required=True)
    employees_sub.add_parser("list", help="Lister").set_defaults(
        func=cmd_employees_list
    )
    employees_sub.add_parser("create", help="Créer").set_defaults(
        func=cmd_employees_create
    )
    _add_id_parser(employees_sub, "update", "Mettre à jour", cmd_employees_update)
    _add_id_parser(employees_sub, "delete", "Supprimer", cmd_employees_delete)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
