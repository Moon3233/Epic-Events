"""Collaborateur Epic Events."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from epic_events.models.base import Base

if TYPE_CHECKING:
    from epic_events.models.client import Client
    from epic_events.models.contract import Contract
    from epic_events.models.department import Department
    from epic_events.models.event import Event


class Employee(Base):
    """Compte collaborateur lié à un département."""

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)

    department: Mapped[Department] = relationship(back_populates="employees")
    clients: Mapped[list[Client]] = relationship(back_populates="sales_contact")
    contracts: Mapped[list[Contract]] = relationship(back_populates="sales_contact")
    supported_events: Mapped[list[Event]] = relationship(back_populates="support_contact")

    def __repr__(self) -> str:
        return (
            f"<Employee id={self.id} number={self.employee_number!r} "
            f"email={self.email!r}>"
        )
