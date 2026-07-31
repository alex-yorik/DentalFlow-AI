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

    if lead.name and lead.name.strip() and (rule := rules.get("has_name")):
        score += rule
        breakdown["has_name"] = rule

    if lead.phone and lead.phone.strip() and (rule := rules.get("has_phone")):
        score += rule
        breakdown["has_phone"] = rule

    if lead.email and lead.email.strip() and (rule := rules.get("has_email")):
        score += rule
        breakdown["has_email"] = rule

    if lead.service_interest and lead.service_interest.strip() and (rule := rules.get("has_service_interest")):
        score += rule
        breakdown["has_service_interest"] = rule

    if lead.preferred_time and lead.preferred_time.strip() and (rule := rules.get("has_preferred_time")):
        score += rule
        breakdown["has_preferred_time"] = rule

    if lead.intent and lead.intent == "new_appointment" and (rule := rules.get("intent_is_new_appointment")):
        score += rule
        breakdown["intent_is_new_appointment"] = rule

    if lead.urgency and lead.urgency == "urgent" and (rule := rules.get("urgency_is_urgent")):
        score += rule
        breakdown["urgency_is_urgent"] = rule

    return QualificationResult(
        qualified=score >= config.crm_write_threshold,
        score=score,
        breakdown=breakdown,
    )