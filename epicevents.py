#!/usr/bin/env python3
"""Point d'entrée CLI (auth + lecture des données)."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from epic_events.auth.session import (  # noqa: E402
    AuthenticationError,
    AuthorizationError,
    get_current_identity,
    login,
    logout,
)
from epic_events.db import session_scope  # noqa: E402
from epic_events.services.clients import list_clients  # noqa: E402
from epic_events.services.contracts import list_contracts  # noqa: E402
from epic_events.services.events import list_events  # noqa: E402


def _print_error(exc: Exception) -> None:
    print(f"Erreur : {exc}", file=sys.stderr)


def cmd_login(_: argparse.Namespace) -> int:
    email = input("Email : ").strip()
    password = getpass.getpass("Mot de passe : ")
    try:
        with session_scope() as session:
            identity = login(session, email=email, password=password)
    except AuthenticationError as exc:
        _print_error(exc)
        return 1

    print(
        f"Connecté : {identity.full_name} "
        f"({identity.department}) — jeton enregistré."
    )
    return 0


def cmd_logout(_: argparse.Namespace) -> int:
    logout()
    print("Déconnecté.")
    return 0


def cmd_whoami(_: argparse.Namespace) -> int:
    try:
        with session_scope() as session:
            identity = get_current_identity(session)
    except AuthenticationError as exc:
        _print_error(exc)
        return 1

    perms = ", ".join(sorted(p.value for p in identity.permissions))
    print(f"Nom      : {identity.full_name}")
    print(f"Email    : {identity.email}")
    print(f"N°       : {identity.employee_number}")
    print(f"Dépt.    : {identity.department}")
    print(f"Droits   : {perms}")
    return 0


def cmd_clients(_: argparse.Namespace) -> int:
    try:
        with session_scope() as session:
            clients = list_clients(session)
            rows = [
                (
                    c.id,
                    c.full_name,
                    c.company_name,
                    c.email,
                    c.phone,
                    c.sales_contact.full_name,
                )
                for c in clients
            ]
    except (AuthenticationError, AuthorizationError) as exc:
        _print_error(exc)
        return 1

    if not rows:
        print("Aucun client.")
        return 0

    print(f"{'ID':<4} {'Nom':<22} {'Entreprise':<22} {'Email':<28} {'Tél.':<18} Commercial")
    print("-" * 120)
    for row in rows:
        print(
            f"{row[0]:<4} {row[1]:<22} {row[2]:<22} {row[3]:<28} {row[4]:<18} {row[5]}"
        )
    return 0


def cmd_contracts(_: argparse.Namespace) -> int:
    try:
        with session_scope() as session:
            contracts = list_contracts(session)
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
    except (AuthenticationError, AuthorizationError) as exc:
        _print_error(exc)
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


def cmd_events(_: argparse.Namespace) -> int:
    try:
        with session_scope() as session:
            events = list_events(session)
            rows = [
                (
                    e.id,
                    e.name,
                    e.contract.client.company_name,
                    e.start_date.strftime("%Y-%m-%d %H:%M"),
                    e.location,
                    e.attendees,
                    e.support_contact.full_name if e.support_contact else "—",
                )
                for e in events
            ]
    except (AuthenticationError, AuthorizationError) as exc:
        _print_error(exc)
        return 1

    if not rows:
        print("Aucun événement.")
        return 0

    print(
        f"{'ID':<4} {'Nom':<28} {'Client':<20} {'Début':<16} "
        f"{'Lieu':<24} {'Pers.':>5} Support"
    )
    print("-" * 120)
    for row in rows:
        print(
            f"{row[0]:<4} {row[1]:<28} {row[2]:<20} {row[3]:<16} "
            f"{row[4]:<24} {row[5]:>5} {row[6]}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="epicevents", description="CRM Epic Events")
    sub = parser.add_subparsers(dest="command", required=True)

    commands = (
        ("login", "S'authentifier et stocker un jeton JWT", cmd_login),
        ("logout", "Supprimer le jeton local", cmd_logout),
        ("whoami", "Afficher la session courante", cmd_whoami),
        ("clients", "Lister tous les clients", cmd_clients),
        ("contracts", "Lister tous les contrats", cmd_contracts),
        ("events", "Lister tous les événements", cmd_events),
    )
    for name, help_text, handler in commands:
        cmd = sub.add_parser(name, help=help_text)
        cmd.set_defaults(func=handler)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
