from src.leads.models import Lead, LeadState
from src.llm.contracts import SuggestedAction
from src.config.loader import QualificationConfig
from src.rules.qualification import calculate_score


ACTION_TO_STATE: dict[SuggestedAction, LeadState] = {
    SuggestedAction.ANSWER_FAQ: LeadState.FAQ_ONLY,
    SuggestedAction.ASK_FIELD: LeadState.COLLECT_FIELDS,
    SuggestedAction.QUALIFY: LeadState.QUALIFYING,
    SuggestedAction.CRM_WRITE: LeadState.CRM_WRITE,
    SuggestedAction.CLOSE: LeadState.CLOSED,
    SuggestedAction.BLOCK: LeadState.BLOCKED,
}


class TransitionResult:
    def __init__(self, allowed: bool, to_state: LeadState | None = None, reason: str | None = None):
        self.allowed = allowed
        self.to_state = to_state
        self.reason = reason


def _has_critical_fields(lead: Lead, config: QualificationConfig) -> bool:
    for field in config.critical_fields:
        if getattr(lead, field, None) is None:
            return False
    return True


_TRANSITION_TABLE: dict[tuple[LeadState, LeadState], str] = {
    (LeadState.NEW, LeadState.FAQ_ONLY): "new → faq: initial faq response",
    (LeadState.NEW, LeadState.COLLECT_FIELDS): "new → collect: lead intent detected",
    (LeadState.NEW, LeadState.CLOSED): "new → closed: no interaction needed",
    (LeadState.NEW, LeadState.BLOCKED): "new → blocked: immediate block",

    (LeadState.FAQ_ONLY, LeadState.COLLECT_FIELDS): "faq → collect: lead intent during faq",
    (LeadState.FAQ_ONLY, LeadState.CLOSED): "faq → closed: faq answered, no lead",
    (LeadState.FAQ_ONLY, LeadState.BLOCKED): "faq → blocked: abuse during faq",

    (LeadState.COLLECT_FIELDS, LeadState.QUALIFYING): "collect → qualifying: all critical fields present",
    (LeadState.COLLECT_FIELDS, LeadState.FOLLOWUP_PENDING): "collect → followup: missing fields, schedule reminder",
    (LeadState.COLLECT_FIELDS, LeadState.CLOSED): "collect → closed: user left",
    (LeadState.COLLECT_FIELDS, LeadState.BLOCKED): "collect → blocked: abuse during collection",

    (LeadState.QUALIFYING, LeadState.CRM_WRITE): "qualifying → crm_write: score >= threshold",
    (LeadState.QUALIFYING, LeadState.CLOSED): "qualifying → closed: not qualified",
    (LeadState.QUALIFYING, LeadState.BLOCKED): "qualifying → blocked: abuse during qualification",

    (LeadState.CRM_WRITE, LeadState.CLOSED): "crm_write → closed: lead written",
    (LeadState.CRM_WRITE, LeadState.BLOCKED): "crm_write → blocked: abuse after crm write",

    (LeadState.FOLLOWUP_PENDING, LeadState.COLLECT_FIELDS): "followup → collect: user responded",
    (LeadState.FOLLOWUP_PENDING, LeadState.CLOSED): "followup → closed: max retries reached",
    (LeadState.FOLLOWUP_PENDING, LeadState.BLOCKED): "followup → blocked: abuse during followup",

    (LeadState.CLOSED, LeadState.BLOCKED): "closed → blocked: post-close block needed",
}


def suggest_state(action: SuggestedAction) -> LeadState:
    return ACTION_TO_STATE[action]


def validate_transition(
    from_state: LeadState,
    to_state: LeadState,
    lead: Lead | None = None,
    config: QualificationConfig | None = None,
) -> TransitionResult:
    key = (from_state, to_state)
    if key not in _TRANSITION_TABLE:
        return TransitionResult(
            allowed=False,
            reason=f"transition {from_state.value} → {to_state.value} not in transition table",
        )

    if to_state == LeadState.QUALIFYING and lead is not None and config is not None:
        if not _has_critical_fields(lead, config):
            return TransitionResult(
                allowed=False,
                reason="missing critical fields for qualification",
            )

    if to_state == LeadState.CRM_WRITE and lead is not None and config is not None:
        qual = calculate_score(lead, config)
        if not qual.qualified:
            return TransitionResult(
                allowed=False,
                reason=f"qualification score {qual.score} < threshold {config.crm_write_threshold}",
            )

    return TransitionResult(allowed=True, to_state=to_state, reason=_TRANSITION_TABLE[key])


def apply_transition(lead: Lead, to_state: LeadState) -> Lead:
    lead.state = to_state
    return lead