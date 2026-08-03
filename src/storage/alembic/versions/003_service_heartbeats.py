"""Add service_heartbeats table for worker monitoring

Revision ID: 003
Revises: 002
Create Date: 2026-08-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "service_heartbeats",
        sa.Column("service", sa.String(length=64), primary_key=True),
        sa.Column("last_beat", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("service_heartbeats")
