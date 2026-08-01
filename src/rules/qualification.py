from src.leads.models import Lead
from src.config.loader import QualificationConfig


class QualificationResult:
    def __init__(self, qualified: bool, score: int, breakdown: dict[str, int]):
        self.qualified = qualified
        self.score = score
        self.breakdown = breakdown


def calculate_score(lead: Lead, config: QualificationConfig) -> QualificationResult:
    score = 0
    breakdown: dict[str, int] = {}
    rules = config.score_rules

    if lead.name and lead.name.strip() and rules.has_name:
        score += rules.has_name
        breakdown["has_name"] = rules.has_name

    if lead.phone and lead.phone.strip() and rules.has_phone:
        score += rules.has_phone
        breakdown["has_phone"] = rules.has_phone

    if lead.email and lead.email.strip() and rules.has_email:
        score += rules.has_email
        breakdown["has_email"] = rules.has_email

    if lead.service_interest and lead.service_interest.strip() and rules.has_service_interest:
        score += rules.has_service_interest
        breakdown["has_service_interest"] = rules.has_service_interest

    if lead.preferred_time and lead.preferred_time.strip() and rules.has_preferred_time:
        score += rules.has_preferred_time
        breakdown["has_preferred_time"] = rules.has_preferred_time

    if lead.intent and lead.intent == "new_appointment" and rules.intent_is_new_appointment:
        score += rules.intent_is_new_appointment
        breakdown["intent_is_new_appointment"] = rules.intent_is_new_appointment

    if lead.urgency and lead.urgency == "urgent" and rules.urgency_is_urgent:
        score += rules.urgency_is_urgent
        breakdown["urgency_is_urgent"] = rules.urgency_is_urgent

    return QualificationResult(
        qualified=score >= config.crm_write_threshold,
        score=score,
        breakdown=breakdown,
    )