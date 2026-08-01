import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict


class BusinessInfo(BaseModel):
    name: str
    address: str
    phone: str
    hours: dict[str, str]
    timezone: str
    staff_chat_id: int
    messages: dict[str, str]


class Service(BaseModel):
    name: str
    description: str
    duration_minutes: int


class FAQItem(BaseModel):
    question_patterns: list[str]
    answer: str


class RulesConfig(BaseModel):
    blocked_phrases: list[str]
    confidence_threshold: float = 0.5
    max_refusal_count: int = 3


class ScoreRules(BaseModel):
    has_name: int = 0
    has_phone: int = 0
    has_email: int = 0
    has_service_interest: int = 0
    has_preferred_time: int = 0
    intent_is_new_appointment: int = 0
    urgency_is_urgent: int = 0

    model_config = ConfigDict(extra='forbid')

    def __contains__(self, item: str) -> bool:
        return item in type(self).model_fields


class QualificationConfig(BaseModel):
    critical_fields: list[str]
    score_rules: ScoreRules
    crm_write_threshold: int


class FollowUpConfig(BaseModel):
    templates: dict[str, str]
    delay_minutes: int = 60
    max_retries: int = 2
    poll_interval_seconds: int = 30


class PromptCollection(BaseModel):
    system: str


class ClientConfig(BaseModel):
    business: BusinessInfo
    services: list[Service]
    faq: list[FAQItem]
    rules: RulesConfig
    qualification: QualificationConfig
    followup: FollowUpConfig
    prompts: PromptCollection


class AppConfig(BaseModel):
    telegram_bot_token: str
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    client_name: str = "demo_dental"
    debug: bool = False
    crm_provider: str = "mock"
    web_port: int = 8080
    web_host: str = "0.0.0.0"
    client: ClientConfig


CLIENTS_DIR = Path(os.getenv("DENTALFLOW_CLIENTS_DIR", "./clients"))


def _load_json(path: Path) -> dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def _load_prompts(client_dir: Path, business: BusinessInfo) -> PromptCollection:
    prompts_dir = client_dir / "prompts"
    if not prompts_dir.is_dir():
        raise FileNotFoundError(f"Prompts directory not found: {prompts_dir}")

    system_path = prompts_dir / "system.md"
    if not system_path.is_file():
        raise FileNotFoundError(f"System prompt not found: {system_path}")

    system_text = system_path.read_text(encoding="utf-8")

    hours_str = "; ".join(
        f"{day}: {hours}" for day, hours in business.hours.items()
    )
    system_text = system_text.replace("{clinic_name}", business.name)
    system_text = system_text.replace("{clinic_address}", business.address)
    system_text = system_text.replace("{clinic_phone}", business.phone)
    system_text = system_text.replace("{clinic_hours}", hours_str)

    return PromptCollection(system=system_text)


def load_client_config(client_name: str) -> ClientConfig:
    client_dir = CLIENTS_DIR / client_name
    if not client_dir.is_dir():
        raise FileNotFoundError(f"Client directory not found: {client_dir}")

    business = BusinessInfo(**_load_json(client_dir / "business.json"))

    return ClientConfig(
        business=business,
        services=[Service(**s) for s in _load_json(client_dir / "services.json")],
        faq=[FAQItem(**f) for f in _load_json(client_dir / "faq.json")],
        rules=RulesConfig(**_load_json(client_dir / "rules.json")),
        qualification=QualificationConfig(**_load_json(client_dir / "qualification.json")),
        followup=FollowUpConfig(**_load_json(client_dir / "followup.json")),
        prompts=_load_prompts(client_dir, business),
    )


def load_config() -> AppConfig:
    client_name = os.getenv("DENTALFLOW_CLIENT", "demo_dental")
    client = load_client_config(client_name)

    return AppConfig(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        client_name=client_name,
        debug=os.getenv("DEBUG", "").lower() in ("1", "true", "yes"),
        crm_provider=os.getenv("DENTALFLOW_CRM_PROVIDER", "mock"),
        web_port=int(os.getenv("DENTALFLOW_PORT", "8080")),
        client=client,
    )