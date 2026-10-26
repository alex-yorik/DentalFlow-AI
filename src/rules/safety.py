import re

from src.config.loader import RulesConfig
from src.llm.contracts import AIOutput, Intent


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


def _phrase_in_text(phrase: str, text: str) -> bool:
    pattern = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
    return bool(pattern.search(text))


def _strip_safe_phrases(text: str, safe_phrases: list[str]) -> str:
    for phrase in safe_phrases:
        if not phrase.strip():
            continue
        pattern = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
        text = pattern.sub('', text)
    return text


def check_safety(output: AIOutput, rules: RulesConfig, lead=None) -> SafetyVerdict:
    checked_reply_text = _strip_safe_phrases(output.reply_text, rules.safe_phrases)
    for phrase in rules.blocked_phrases:
        if _phrase_in_text(phrase, checked_reply_text):
            return _build_refusal_verdict(
                f"reply contains blocked phrase: '{phrase}'", lead, rules,
            )

    for field in output.extracted_fields:
        for phrase in rules.blocked_phrases:
            if _phrase_in_text(phrase, field.value):
                return _build_refusal_verdict(
                    f"extracted field '{field.field_name}' contains blocked phrase: '{phrase}'", lead, rules,
                )

    if output.intent == Intent.UNSAFE and not output.safe:
        return _build_refusal_verdict(
            "AI classified interaction as unsafe", lead, rules,
        )

    return SafetyVerdict(allowed=True)
