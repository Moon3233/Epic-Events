"""Département / rôle d'un collaborateur (gestion, commercial, support)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from epic_events.models.base import Base

if TYPE_CHECKING:
    from epic_events.models.employee import Employee


class Department(Base):
    """Rôle métier — table dédiée (évite de coder les rôles en dur sur Employee)."""

    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    employees: Mapped[list[Employee]] = relationship(back_populates="department")

    def __repr__(self) -> str:
        return f"<Department id={self.id} name={self.name!r}>"
