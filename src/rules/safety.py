from src.llm.contracts import AIOutput, Intent
from src.config.loader import RulesConfig


class SafetyVerdict:
    def __init__(self, allowed: bool, blocked_reason: str | None = None, escalate: bool = False):
        self.allowed = allowed
        self.blocked_reason = blocked_reason
        self.escalate = escalate


def check_safety(output: AIOutput, rules: RulesConfig) -> SafetyVerdict:
    reply_lower = output.reply_text.lower()
    for phrase in rules.blocked_phrases:
        if phrase in reply_lower:
            return SafetyVerdict(
                allowed=False,
                blocked_reason=f"reply contains blocked phrase: '{phrase}'",
                escalate=True,
            )

    for field in output.extracted_fields:
        field_lower = field.value.lower()
        for phrase in rules.blocked_phrases:
            if phrase in field_lower:
                return SafetyVerdict(
                    allowed=False,
                    blocked_reason=f"extracted field '{field.field_name}' contains blocked phrase: '{phrase}'",
                    escalate=True,
                )

    if output.intent == Intent.UNSAFE and not output.safe:
        return SafetyVerdict(
            allowed=False,
            blocked_reason="AI classified interaction as unsafe",
            escalate=True,
        )

    return SafetyVerdict(allowed=True)