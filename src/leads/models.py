import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LeadState(str, enum.Enum):
    NEW = "new"
    FAQ_ONLY = "faq_only"
    COLLECT_FIELDS = "collect_fields"
    QUALIFYING = "qualifying"
    CRM_WRITE = "crm_write"
    CLOSED = "closed"
    BLOCKED = "blocked"
    FOLLOWUP_PENDING = "followup_pending"


class Lead(BaseModel):
    id: str
    telegram_chat_id: int
    state: LeadState = LeadState.NEW
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    service_interest: Optional[str] = None
    intent: Optional[str] = None
    urgency: Optional[str] = None
    preferred_time: Optional[str] = None
    source: str = "telegram"
    qualification_score: int = 0
    conversation_summary: str = ""
    opt_in_consent: bool = False
    internal_tags: list[str] = []
    crm_contact_id: Optional[str] = None
    followup_task_id: Optional[str] = None
    refusal_count: int = 0
    created_at: datetime
    updated_at: datetime