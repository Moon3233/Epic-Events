"""Client Epic Events."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from epic_events.models.base import Base

if TYPE_CHECKING:
    from epic_events.models.contract import Contract
    from epic_events.models.employee import Employee


class Client(Base):
    """Fiche client suivie par un commercial."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    company_name: Mapped[str] = mapped_column(String(150), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    sales_contact_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"),
        nullable=False,
    )

    sales_contact: Mapped[Employee] = relationship(back_populates="clients")
    contracts: Mapped[list[Contract]] = relationship(back_populates="client")

    def __repr__(self) -> str:
        return f"<Client id={self.id} company={self.company_name!r}>"
