"""Application Click racine."""

from __future__ import annotations

import click

from epic_events import __version__
from epic_events.cli.auth_commands import login_cmd, logout_cmd, whoami_cmd
from epic_events.cli.clients_commands import clients_group
from epic_events.cli.contracts_commands import contracts_group
from epic_events.cli.employees_commands import employees_group
from epic_events.cli.events_commands import events_group


@click.group()
@click.version_option(version=__version__, prog_name="epicevents")
def cli() -> None:
    """CRM Epic Events — gestion clients, contrats et événements."""


cli.add_command(login_cmd)
cli.add_command(logout_cmd)
cli.add_command(whoami_cmd)
cli.add_command(clients_group)
cli.add_command(contracts_group)
cli.add_command(employees_group)
cli.add_command(events_group)
