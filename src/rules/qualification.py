from src.leads.models import Lead
from src.config.loader import QualificationConfig, ScoringRule


class QualificationResult:
    def __init__(self, qualified: bool, score: int, breakdown: dict[str, int]):
        self.qualified = qualified
        self.score = score
        self.breakdown = breakdown


def _rule_matches(lead: Lead, rule: ScoringRule) -> bool:
    value = getattr(lead, rule.attribute, None)
    if rule.match == "presence":
        return bool(value and str(value).strip())
    if rule.match == "equals":
        return value is not None and value == rule.value
    return False


def calculate_score(lead: Lead, config: QualificationConfig) -> QualificationResult:
    score = 0
    breakdown: dict[str, int] = {}
    rules = config.score_rules

    for key, rule_def in rules.rule_map.items():
        points = getattr(rules, key, None)
        if points is None:
            points = rules.custom_points.get(key, 0)
        if points and _rule_matches(lead, rule_def):
            score += points
            breakdown[key] = points

    return QualificationResult(
        qualified=score >= config.crm_write_threshold,
        score=score,
        breakdown=breakdown,
    )