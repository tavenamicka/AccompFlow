"""create interventions

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interventions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("date_intervention", sa.Date(), nullable=False),
        sa.Column("niveau", sa.String(length=2), nullable=False),
        sa.Column("duree_minutes", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("groupe_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("niveau IN ('N1', 'N2', 'N3')", name="ck_interventions_niveau"),
        sa.CheckConstraint("duree_minutes > 0", name="ck_interventions_duree_positive"),
    )
    op.create_index("ix_interventions_client_id", "interventions", ["client_id"])


def downgrade() -> None:
    op.drop_table("interventions")
