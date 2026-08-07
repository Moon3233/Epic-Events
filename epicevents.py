#!/usr/bin/env python3
"""Point d'entrée CLI minimal (login / logout / whoami)."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

# Permet d'exécuter depuis la racine du dépôt sans installation editable
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from epic_events.auth.session import (  # noqa: E402
    AuthenticationError,
    get_current_identity,
    login,
    logout,
)
from epic_events.db import session_scope  # noqa: E402


def cmd_login(_: argparse.Namespace) -> int:
    email = input("Email : ").strip()
    password = getpass.getpass("Mot de passe : ")
    try:
        with session_scope() as session:
            identity = login(session, email=email, password=password)
    except AuthenticationError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
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
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1

    perms = ", ".join(sorted(p.value for p in identity.permissions))
    print(f"Nom      : {identity.full_name}")
    print(f"Email    : {identity.email}")
    print(f"N°       : {identity.employee_number}")
    print(f"Dépt.    : {identity.department}")
    print(f"Droits   : {perms}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="epicevents", description="CRM Epic Events")
    sub = parser.add_subparsers(dest="command", required=True)

    p_login = sub.add_parser("login", help="S'authentifier et stocker un jeton JWT")
    p_login.set_defaults(func=cmd_login)

    p_logout = sub.add_parser("logout", help="Supprimer le jeton local")
    p_logout.set_defaults(func=cmd_logout)

    p_whoami = sub.add_parser("whoami", help="Afficher la session courante")
    p_whoami.set_defaults(func=cmd_whoami)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
