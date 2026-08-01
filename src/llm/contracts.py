import enum
from typing import Optional

from pydantic import BaseModel, Field


class Intent(str, enum.Enum):
    FAQ = "faq"
    LEAD = "lead"
    OFF_TOPIC = "off_topic"
    UNSAFE = "unsafe"


class SuggestedAction(str, enum.Enum):
    ANSWER_FAQ = "answer_faq"
    ASK_FIELD = "ask_field"
    QUALIFY = "qualify"
    CRM_WRITE = "crm_write"
    CLOSE = "close"
    BLOCK = "block"


class ExtractedField(BaseModel):
    field_name: str = Field(description="One of: name, phone, email, service, urgency, preferred_time")
    value: str = Field(description="The extracted value")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0–1.0")


class AIOutput(BaseModel):
    intent: Intent = Field(description="User intent classification")
    confidence: float = Field(ge=0.0, le=1.0, description="Overall confidence in this analysis")
    reply_text: str = Field(description="The reply to show the user")
    is_lead: bool = Field(description="Whether the user is a potential lead")
    extracted_fields: list[ExtractedField] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    suggested_action: SuggestedAction = Field(description="Next action to take")
    safe: bool = Field(description="Whether the request and reply are safe")
    crm_write_allowed: bool = Field(description="Whether CRM write is appropriate")
    schedule_followup: bool = Field(description="Whether to schedule a follow-up")
    escalation_needed: bool = Field(description="Whether to notify a human")
    escalation_reason: Optional[str] = Field(default=None)
    is_fallback: bool = False


class AIInput(BaseModel):
    system_prompt: str = Field(description="Full system prompt with clinic context")
    user_message: str = Field(description="The user's latest message")
    conversation_context: str = Field(
        default="",
        description="Lead state, extracted fields, conversation summary so far",
    )