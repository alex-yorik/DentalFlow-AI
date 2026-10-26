"""Add messages + appointments tables for dialog context & reschedule

Revision ID: 004
Revises: 003
Create Date: 2026-08-04
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "messages",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("channel_user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_messages_channel_time", "messages", ["channel_user_id", "created_at"])

    op.create_table(
        "appointments",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("lead_id", sa.Text(), nullable=True),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("service", sa.Text(), nullable=True),
        sa.Column("appointment_datetime", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="scheduled"),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_appointments_phone", "appointments", ["phone"])
    op.create_index("idx_appointments_name", "appointments", ["name"])


def downgrade() -> None:
    op.drop_table("appointments")
    op.drop_table("messages")
