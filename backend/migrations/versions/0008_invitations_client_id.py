"""invitations: add client_id (lien vers une fiche client existante)

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("invitations", sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=True))


def downgrade() -> None:
    op.drop_column("invitations", "client_id")
