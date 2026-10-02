from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Echeancier(Base):
    __tablename__ = "echeanciers"
    __table_args__ = (CheckConstraint("type_echeance IN ('pack', 'formation', 'autre')", name="ck_echeanciers_type"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False, index=True)
    titre: Mapped[str] = mapped_column(String(200), nullable=False)
    type_echeance: Mapped[str] = mapped_column(String(20), nullable=False, default="autre")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    client = relationship("Client")
    echeances = relationship(
        "Echeance",
        cascade="all, delete-orphan",
        order_by="Echeance.id",
        back_populates="echeancier",
    )


class Echeance(Base):
    __tablename__ = "echeances"
    __table_args__ = (CheckConstraint("statut IN ('attente', 'paye')", name="ck_echeances_statut"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    echeancier_id: Mapped[int] = mapped_column(ForeignKey("echeanciers.id", ondelete="CASCADE"), nullable=False, index=True)
    date_facturation: Mapped[Optional[date]] = mapped_column(Date)
    date_echeance: Mapped[Optional[date]] = mapped_column(Date)
    montant: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    numero_facture: Mapped[Optional[str]] = mapped_column(String(50))
    statut: Mapped[str] = mapped_column(String(10), nullable=False, default="attente")
    date_paiement: Mapped[Optional[date]] = mapped_column(Date)
    note: Mapped[Optional[str]] = mapped_column(Text)

    echeancier = relationship("Echeancier", back_populates="echeances")

    @property
    def en_retard(self) -> bool:
        # Calculé à la lecture, jamais stocké : une échéance « en attente »
        # dont la date est dépassée est en retard, sans tâche de fond.
        return self.statut == "attente" and self.date_echeance is not None and self.date_echeance < date.today()
