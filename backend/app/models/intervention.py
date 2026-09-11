import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Intervention(Base):
    __tablename__ = "interventions"
    __table_args__ = (
        CheckConstraint("niveau IN ('N1', 'N2', 'N3')", name="ck_interventions_niveau"),
        CheckConstraint("duree_minutes > 0", name="ck_interventions_duree_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    date_intervention: Mapped[date] = mapped_column(Date, nullable=False)
    niveau: Mapped[str] = mapped_column(String(2), nullable=False)
    duree_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # `Uuid` générique (SQLAlchemy 2.0) plutôt que `postgresql.UUID` (ForfaitFlow) :
    # rendu natif sur Postgres en prod, mais aussi compilable sur le SQLite
    # in-memory utilisé par la suite de tests d'AccompFlow.
    groupe_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
