from src.config.loader import RulesConfig
from src.llm.contracts import AIOutput, Intent, SuggestedAction
from src.rules.validator import validate_ai_output

RULES = RulesConfig(
    blocked_phrases=[],
    confidence_threshold=0.5,
    max_refusal_count=3,
)


def _output(**kwargs) -> AIOutput:
    defaults = {
        "intent": Intent.FAQ,
        "confidence": 0.95,
        "reply_text": "We are open Mon-Fri.",
        "is_lead": False,
        "extracted_fields": [],
        "missing_fields": [],
        "suggested_action": SuggestedAction.ANSWER_FAQ,
        "safe": True,
        "crm_write_allowed": False,
        "schedule_followup": False,
        "escalation_needed": False,
    }
    defaults.update(kwargs)
    return AIOutput(**defaults)


class TestValidator:
    def test_valid_output_passes(self):
        result = validate_ai_output(_output(), RULES)
        assert result.valid
        assert result.reason is None

    def test_low_confidence_rejected(self):
        result = validate_ai_output(_output(confidence=0.3), RULES)
        assert not result.valid
        assert "confidence" in (result.reason or "").lower()

    def test_confidence_at_threshold_passes(self):
        result = validate_ai_output(_output(confidence=0.5), RULES)
        assert result.valid

    def test_lead_with_close_rejected(self):
        result = validate_ai_output(
            _output(is_lead=True, suggested_action=SuggestedAction.CLOSE),
            RULES,
        )
        assert not result.valid
        assert "is_lead" in (result.reason or "").lower()

    def test_lead_with_answer_faq_rejected(self):
        result = validate_ai_output(
            _output(is_lead=True, suggested_action=SuggestedAction.ANSWER_FAQ),
            RULES,
        )
        assert not result.valid

    def test_non_lead_with_qualify_rejected(self):
        result = validate_ai_output(
            _output(is_lead=False, suggested_action=SuggestedAction.QUALIFY),
            RULES,
        )
        assert not result.valid
        assert "is_lead" in (result.reason or "").lower()

    def test_non_lead_with_crm_write_rejected(self):
        result = validate_ai_output(
            _output(is_lead=False, suggested_action=SuggestedAction.CRM_WRITE),
            RULES,
        )
        assert not result.valid

    def test_unsafe_intent_with_safe_flag_inconsistent(self):
        result = validate_ai_output(
            _output(intent=Intent.UNSAFE, safe=True),
            RULES,
        )
        assert not result.valid
        assert "inconsistent" in (result.reason or "").lower()

    def test_unsafe_intent_not_safe_consistent(self):
        result = validate_ai_output(
            _output(intent=Intent.UNSAFE, safe=False),
            RULES,
        )
        assert result.valid

    def test_faq_lead_with_ask_field_passes(self):
        result = validate_ai_output(
            _output(is_lead=True, suggested_action=SuggestedAction.ASK_FIELD),
            RULES,
        )
        assert result.valid

    def test_off_topic_intent_with_close_passes(self):
        result = validate_ai_output(
            _output(intent=Intent.OFF_TOPIC, suggested_action=SuggestedAction.CLOSE),
            RULES,
        )
        assert result.valid
