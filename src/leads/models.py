import enum
import logging
import re
from datetime import datetime

from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)

PHONE_PATTERN = re.compile(r'^[\d\s\-\+\(\)]{7,20}$')
EMAIL_PATTERN = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')


class LeadState(enum.StrEnum):
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
    channel_user_id: int
    state: LeadState = LeadState.NEW
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    service_interest: str | None = None
    intent: str | None = None
    urgency: str | None = None
    preferred_time: str | None = None
    source: str = "telegram"
    channel_type: str = "telegram"
    qualification_score: int = 0
    conversation_summary: str = ""
    opt_in_consent: bool = False
    internal_tags: list[str] = []
    crm_contact_id: str | None = None
    followup_task_id: str | None = None
    refusal_count: int = 0
    created_at: datetime
    updated_at: datetime

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not PHONE_PATTERN.match(v):
            raise ValueError(f"Invalid phone format: {v}")
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not EMAIL_PATTERN.match(v):
            raise ValueError(f"Invalid email format: {v}")
        return v
