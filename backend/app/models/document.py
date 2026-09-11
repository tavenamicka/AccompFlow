from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint("document_type IN ('facture', 'rapport_intervention', 'autre')", name="ck_documents_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Dénormalisé : renseigné automatiquement quand le document appartient à un
    # compte lié à une fiche client (voir services/rapports_documents.py),
    # permet de naviguer Client -> Documents sans jointure via User.
    client_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clients.id"), nullable=True, index=True)
    document_type: Mapped[str] = mapped_column(String(30), default="autre", nullable=False)
    # Format "yyyy-mm" : référence la période anniversaire calculée par
    # services/periode.py (jamais stockée en base) — NULL pour facture/autre.
    period_label: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(127), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="documents")
