from src.llm.contracts import AIOutput, Intent
from src.config.loader import RulesConfig


class SafetyVerdict:
    def __init__(self, allowed: bool, blocked_reason: str | None = None, escalate: bool = False):
        self.allowed = allowed
        self.blocked_reason = blocked_reason
        self.escalate = escalate


def _build_refusal_verdict(reason: str, lead, rules: RulesConfig) -> SafetyVerdict:
    if lead is not None:
        lead.refusal_count += 1
        if lead.refusal_count >= rules.max_refusal_count:
            return SafetyVerdict(allowed=False, blocked_reason=reason, escalate=True)
        return SafetyVerdict(allowed=False, blocked_reason=reason, escalate=False)
    return SafetyVerdict(allowed=False, blocked_reason=reason, escalate=True)


def check_safety(output: AIOutput, rules: RulesConfig, lead=None) -> SafetyVerdict:
    reply_lower = output.reply_text.lower()
    for phrase in rules.blocked_phrases:
        if phrase in reply_lower:
            return _build_refusal_verdict(
                f"reply contains blocked phrase: '{phrase}'", lead, rules,
            )

    for field in output.extracted_fields:
        field_lower = field.value.lower()
        for phrase in rules.blocked_phrases:
            if phrase in field_lower:
                return _build_refusal_verdict(
                    f"extracted field '{field.field_name}' contains blocked phrase: '{phrase}'", lead, rules,
                )

    if output.intent == Intent.UNSAFE and not output.safe:
        return _build_refusal_verdict(
            "AI classified interaction as unsafe", lead, rules,
        )

    return SafetyVerdict(allowed=True)