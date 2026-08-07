"""Contrat liant un client à Epic Events."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from epic_events.models.base import Base

if TYPE_CHECKING:
    from epic_events.models.client import Client
    from epic_events.models.employee import Employee
    from epic_events.models.event import Event


class Contract(Base):
    """Contrat commercial (montants + statut de signature)."""

    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    sales_contact_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"),
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    remaining_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    is_signed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    client: Mapped[Client] = relationship(back_populates="contracts")
    sales_contact: Mapped[Employee] = relationship(back_populates="contracts")
    event: Mapped[Event | None] = relationship(
        back_populates="contract",
        uselist=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Contract id={self.id} client_id={self.client_id} "
            f"signed={self.is_signed}>"
        )
