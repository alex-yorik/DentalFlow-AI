import json
import os
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


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
    safe_phrases: list[str] = Field(default_factory=list)


class ScoringRule(BaseModel):
    attribute: str
    match: Literal["presence", "equals"]
    value: Optional[str] = None


def _default_rule_map() -> dict[str, ScoringRule]:
    return {
        "has_name": ScoringRule(attribute="name", match="presence"),
        "has_phone": ScoringRule(attribute="phone", match="presence"),
        "has_email": ScoringRule(attribute="email", match="presence"),
        "has_service_interest": ScoringRule(attribute="service_interest", match="presence"),
        "has_preferred_time": ScoringRule(attribute="preferred_time", match="presence"),
        "intent_is_new_appointment": ScoringRule(attribute="intent", match="equals", value="new_appointment"),
        "urgency_is_urgent": ScoringRule(attribute="urgency", match="equals", value="urgent"),
    }


class ScoreRules(BaseModel):
    has_name: int = 0
    has_phone: int = 0
    has_email: int = 0
    has_service_interest: int = 0
    has_preferred_time: int = 0
    intent_is_new_appointment: int = 0
    urgency_is_urgent: int = 0
    custom_points: dict[str, int] = Field(default_factory=dict)
    rule_map: dict[str, ScoringRule] = Field(default_factory=_default_rule_map)

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


class BackupConfig(BaseModel):
    backup_interval_hours: int = 24
    retention_days: int = 7


class MonitoringConfig(BaseModel):
    watchdog_interval: int = 30
    heartbeat_interval: int = 30
    alerts_chat_id: Optional[int] = None
    alert_cooldown_minutes: int = 15
    web_health_url: str = "http://localhost:8080/health"


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
    base_url: str | None = None
    client_name: str = "demo_dental"
    debug: bool = False
    log_level: str = "INFO"
    crm_provider: str = "mock"
    web_port: int = 8080
    # Container must bind all interfaces; nginx is the external entrypoint.
    web_host: str = "0.0.0.0"  # nosec B104
    cors_allow_origins: list[str] = Field(default_factory=list)
    client: ClientConfig
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    backup: BackupConfig = Field(default_factory=BackupConfig)


CLIENTS_DIR = Path(os.getenv("DENTALFLOW_CLIENTS_DIR", "./clients"))


def _load_json(path: Path) -> Any:
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


REQUIRED_ENV_VARS = ("TELEGRAM_BOT_TOKEN", "OPENAI_API_KEY")


def validate_required_env() -> None:
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var, "").strip()]
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )


def load_config() -> AppConfig:
    validate_required_env()
    client_name = os.getenv("DENTALFLOW_CLIENT", "demo_dental")
    client = load_client_config(client_name)

    return AppConfig(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        base_url=os.getenv("OPENAI_BASE_URL") or None,
        client_name=client_name,
        debug=os.getenv("DEBUG", "").lower() in ("1", "true", "yes"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        crm_provider=os.getenv("DENTALFLOW_CRM_PROVIDER", "mock"),
        web_port=int(os.getenv("DENTALFLOW_PORT", "8080")),
        cors_allow_origins=[
            origin.strip()
            for origin in os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
            if origin.strip()
        ],
        client=client,
        monitoring=MonitoringConfig(
            watchdog_interval=int(os.getenv("WATCHDOG_INTERVAL", "30")),
            heartbeat_interval=int(os.getenv("HEARTBEAT_INTERVAL", "30")),
            alerts_chat_id=int(os.getenv("ALERTS_CHAT_ID", "0")) or None,
            alert_cooldown_minutes=int(os.getenv("ALERT_COOLDOWN_MINUTES", "15")),
            web_health_url=os.getenv("WATCHDOG_WEB_URL", "http://localhost:8080/health"),
        ),
        backup=BackupConfig(
            backup_interval_hours=int(os.getenv("BACKUP_INTERVAL_HOURS", "24")),
            retention_days=int(os.getenv("BACKUP_RETENTION_DAYS", "7")),
        ),
    )