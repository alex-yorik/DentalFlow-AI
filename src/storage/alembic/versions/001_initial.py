"""Initial schema: leads + followup_tasks

Revision ID: 001
Revises:
Create Date: 2026-08-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("telegram_chat_id", sa.Integer(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False, server_default="new"),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("service_interest", sa.Text(), nullable=True),
        sa.Column("intent", sa.Text(), nullable=True),
        sa.Column("urgency", sa.Text(), nullable=True),
        sa.Column("preferred_time", sa.Text(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False, server_default="telegram"),
        sa.Column("channel_type", sa.Text(), nullable=False, server_default="telegram"),
        sa.Column("qualification_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("conversation_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("opt_in_consent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("internal_tags", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("crm_contact_id", sa.Text(), nullable=True),
        sa.Column("followup_task_id", sa.Text(), nullable=True),
        sa.Column("refusal_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_leads_telegram_chat_id", "leads", ["telegram_chat_id"])
    op.create_index("idx_leads_state", "leads", ["state"])

    op.create_table(
        "followup_tasks",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("lead_id", sa.Text(), nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("next_run_at", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_followup_tasks_status", "followup_tasks", ["status"])
    op.create_index("idx_followup_tasks_lead", "followup_tasks", ["lead_id"])


def downgrade() -> None:
    op.drop_table("followup_tasks")
    op.drop_table("leads")