"""Rename telegram_chat_id to channel_user_id

Revision ID: 002
Revises: 001
Create Date: 2026-08-03
"""
from collections.abc import Sequence

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("leads", "telegram_chat_id", new_column_name="channel_user_id")
    op.drop_index("idx_leads_telegram_chat_id", table_name="leads")
    op.create_index("idx_leads_channel_user_id", "leads", ["channel_user_id"])


def downgrade() -> None:
    op.drop_index("idx_leads_channel_user_id", table_name="leads")
    op.alter_column("leads", "channel_user_id", new_column_name="telegram_chat_id")
    op.create_index("idx_leads_telegram_chat_id", "leads", ["telegram_chat_id"])
