from src.llm.contracts import AIOutput, Intent, SuggestedAction, ExtractedField
from src.config.loader import RulesConfig
from src.rules.safety import check_safety

RULES = RulesConfig(
    blocked_phrases=["price", "cost", "cheap", "discount", "free", "guarantee", "diagnosis", "prescription",
                     "painkiller", "antibiotic", "cure", "heal", "natural remedy"],
    confidence_threshold=0.5,
    max_refusal_count=3,
)


def _output(**kwargs) -> AIOutput:
    defaults = dict(
        intent=Intent.FAQ,
        confidence=0.95,
        reply_text="We are open Mon-Fri.",
        is_lead=False,
        extracted_fields=[],
        missing_fields=[],
        suggested_action=SuggestedAction.ANSWER_FAQ,
        safe=True,
        crm_write_allowed=False,
        schedule_followup=False,
        escalation_needed=False,
    )
    defaults.update(kwargs)
    return AIOutput(**defaults)


class TestSafetyCheck:
    def test_safe_output_allowed(self):
        verdict = check_safety(_output(), RULES)
        assert verdict.allowed
        assert verdict.blocked_reason is None
        assert not verdict.escalate

    def test_price_in_reply_blocked(self):
        verdict = check_safety(_output(reply_text="The price is $100"), RULES)
        assert not verdict.allowed
        assert "price" in (verdict.blocked_reason or "")
        assert verdict.escalate

    def test_guarantee_in_reply_blocked(self):
        verdict = check_safety(_output(reply_text="We guarantee results"), RULES)
        assert not verdict.allowed
        assert "guarantee" in (verdict.blocked_reason or "")

    def test_diagnosis_in_reply_blocked(self):
        verdict = check_safety(_output(reply_text="I can give you a diagnosis"), RULES)
        assert not verdict.allowed
        assert "diagnosis" in (verdict.blocked_reason or "")

    def test_cost_in_extracted_field_blocked(self):
        output = _output(
            extracted_fields=[ExtractedField(field_name="service", value="cheap whitening", confidence=0.8)],
        )
        verdict = check_safety(output, RULES)
        assert not verdict.allowed
        assert "cheap" in (verdict.blocked_reason or "")

    def test_discount_in_extracted_field_blocked(self):
        output = _output(
            extracted_fields=[ExtractedField(field_name="service", value="discount cleaning", confidence=0.7)],
        )
        verdict = check_safety(output, RULES)
        assert not verdict.allowed
        assert "discount" in (verdict.blocked_reason or "")

    def test_unsafe_intent_not_safe_blocked(self):
        verdict = check_safety(
            _output(intent=Intent.UNSAFE, safe=False, reply_text="I can't help with that"),
            RULES,
        )
        assert not verdict.allowed
        assert "unsafe" in (verdict.blocked_reason or "")

    def test_unsafe_intent_but_safe_flag_not_blocked(self):
        verdict = check_safety(
            _output(intent=Intent.UNSAFE, safe=True, reply_text="I can't help with that"),
            RULES,
        )
        assert verdict.allowed

    def test_prescription_blocked(self):
        verdict = check_safety(_output(reply_text="I can write a prescription for you"), RULES)
        assert not verdict.allowed
        assert "prescription" in (verdict.blocked_reason or "")

    def test_cure_blocked(self):
        verdict = check_safety(_output(reply_text="This will cure your pain"), RULES)
        assert not verdict.allowed
        assert "cure" in (verdict.blocked_reason or "")

    def test_faq_about_hours_not_blocked(self):
        verdict = check_safety(
            _output(reply_text="We are open Monday through Friday from 8 AM to 5 PM."),
            RULES,
        )
        assert verdict.allowed