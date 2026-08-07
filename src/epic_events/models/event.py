"""Événement organisé pour un client (via son contrat signé)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from epic_events.models.base import Base

if TYPE_CHECKING:
    from epic_events.models.contract import Contract
    from epic_events.models.employee import Employee


class Event(Base):
    """Événement : dates, lieu, support assigné (optionnel au départ)."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contract_id: Mapped[int] = mapped_column(
        ForeignKey("contracts.id"),
        unique=True,
        nullable=False,
    )
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    support_contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id"),
        nullable=True,
    )
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    attendees: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    contract: Mapped[Contract] = relationship(back_populates="event")
    support_contact: Mapped[Employee | None] = relationship(
        back_populates="supported_events",
    )

    def __repr__(self) -> str:
        return f"<Event id={self.id} name={self.name!r}>"
