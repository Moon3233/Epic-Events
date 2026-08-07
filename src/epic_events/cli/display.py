"""Rendu Rich (tableaux, messages de succès)."""

from __future__ import annotations

from rich.table import Table

from epic_events.cli.utils import console
from epic_events.models.client import Client
from epic_events.models.contract import Contract
from epic_events.models.employee import Employee
from epic_events.models.event import Event
from epic_events.services.employees import EmployeeIdentity


def success(message: str) -> None:
    console.print(f"[bold green]✓[/bold green] {message}")


def info(message: str) -> None:
    console.print(f"[cyan]{message}[/cyan]")


def render_identity(identity: EmployeeIdentity) -> None:
    table = Table(title="Session", show_header=False, box=None, padding=(0, 2))
    table.add_row("Nom", identity.full_name)
    table.add_row("Email", identity.email)
    table.add_row("N°", identity.employee_number)
    table.add_row("Département", identity.department)
    table.add_row(
        "Permissions",
        ", ".join(sorted(p.value for p in identity.permissions)),
    )
    console.print(table)


def render_employees(employees: list[Employee]) -> None:
    if not employees:
        info("Aucun collaborateur.")
        return
    table = Table(title="Collaborateurs", show_lines=False)
    table.add_column("ID", style="bold")
    table.add_column("N°")
    table.add_column("Nom")
    table.add_column("Email")
    table.add_column("Département")
    for employee in employees:
        table.add_row(
            str(employee.id),
            employee.employee_number,
            employee.full_name,
            employee.email,
            employee.department.name,
        )
    console.print(table)


def render_clients(clients: list[Client]) -> None:
    if not clients:
        info("Aucun client.")
        return
    table = Table(title="Clients")
    table.add_column("ID", style="bold")
    table.add_column("Nom")
    table.add_column("Entreprise")
    table.add_column("Email")
    table.add_column("Téléphone")
    table.add_column("Commercial")
    for client in clients:
        table.add_row(
            str(client.id),
            client.full_name,
            client.company_name,
            client.email,
            client.phone,
            client.sales_contact.full_name,
        )
    console.print(table)


def render_contracts(contracts: list[Contract]) -> None:
    if not contracts:
        info("Aucun contrat.")
        return
    table = Table(title="Contrats")
    table.add_column("ID", style="bold")
    table.add_column("Client")
    table.add_column("Commercial")
    table.add_column("Total", justify="right")
    table.add_column("Reste", justify="right")
    table.add_column("Statut")
    for contract in contracts:
        status = "[green]signé[/green]" if contract.is_signed else "[yellow]non signé[/yellow]"
        table.add_row(
            str(contract.id),
            contract.client.company_name,
            contract.sales_contact.full_name,
            f"{contract.total_amount}",
            f"{contract.remaining_amount}",
            status,
        )
    console.print(table)


def render_events(events: list[Event]) -> None:
    if not events:
        info("Aucun événement.")
        return
    table = Table(title="Événements")
    table.add_column("ID", style="bold")
    table.add_column("Nom")
    table.add_column("Client")
    table.add_column("Début")
    table.add_column("Lieu")
    table.add_column("Pers.", justify="right")
    table.add_column("Support")
    for event in events:
        support = event.support_contact.full_name if event.support_contact else "—"
        table.add_row(
            str(event.id),
            event.name,
            event.contract.client.company_name,
            event.start_date.strftime("%Y-%m-%d %H:%M"),
            event.location,
            str(event.attendees),
            support,
        )
    console.print(table)
