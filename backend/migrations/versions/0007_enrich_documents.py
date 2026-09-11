"""enrich documents: client_id, document_type, period_label

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=True))
    op.add_column(
        "documents",
        sa.Column("document_type", sa.String(length=30), nullable=False, server_default="autre"),
    )
    op.add_column("documents", sa.Column("period_label", sa.String(length=7), nullable=True))
    op.create_index("ix_documents_client_id", "documents", ["client_id"])
    op.create_check_constraint(
        "ck_documents_type", "documents", "document_type IN ('facture', 'rapport_intervention', 'autre')"
    )


def downgrade() -> None:
    op.drop_constraint("ck_documents_type", "documents", type_="check")
    op.drop_index("ix_documents_client_id", table_name="documents")
    op.drop_column("documents", "period_label")
    op.drop_column("documents", "document_type")
    op.drop_column("documents", "client_id")
