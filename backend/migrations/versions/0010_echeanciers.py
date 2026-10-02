"""echeanciers: option par client + tables echeanciers/echeances

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clients", sa.Column("echeanciers_actif", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        "echeanciers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("titre", sa.String(length=200), nullable=False),
        sa.Column("type_echeance", sa.String(length=20), nullable=False, server_default="autre"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("type_echeance IN ('pack', 'formation', 'autre')", name="ck_echeanciers_type"),
    )
    op.create_index("ix_echeanciers_client_id", "echeanciers", ["client_id"])

    op.create_table(
        "echeances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("echeancier_id", sa.Integer(), sa.ForeignKey("echeanciers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date_facturation", sa.Date(), nullable=True),
        sa.Column("date_echeance", sa.Date(), nullable=True),
        sa.Column("montant", sa.Numeric(10, 2), nullable=True),
        sa.Column("numero_facture", sa.String(length=50), nullable=True),
        sa.Column("statut", sa.String(length=10), nullable=False, server_default="attente"),
        sa.Column("date_paiement", sa.Date(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.CheckConstraint("statut IN ('attente', 'paye')", name="ck_echeances_statut"),
    )
    op.create_index("ix_echeances_echeancier_id", "echeances", ["echeancier_id"])


def downgrade() -> None:
    op.drop_index("ix_echeances_echeancier_id", table_name="echeances")
    op.drop_table("echeances")
    op.drop_index("ix_echeanciers_client_id", table_name="echeanciers")
    op.drop_table("echeanciers")
    op.drop_column("clients", "echeanciers_actif")
