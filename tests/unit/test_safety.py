from datetime import datetime, timezone

import pytest

from src.llm.contracts import AIOutput, Intent, SuggestedAction, ExtractedField
from src.config.loader import RulesConfig
from src.leads.models import Lead
from src.rules.safety import check_safety

RULES = RulesConfig(
    blocked_phrases=["price", "cost", "cheap", "discount", "free", "guarantee", "diagnosis", "prescription",
                     "painkiller", "antibiotic", "cure", "heal", "natural remedy"],
    confidence_threshold=0.5,
    max_refusal_count=3,
)

SAFE_PHRASES_RULES = RulesConfig(
    blocked_phrases=["price", "cost", "cheap", "discount", "free", "guarantee", "diagnosis", "prescription",
                     "painkiller", "antibiotic", "cure", "heal", "natural remedy"],
    confidence_threshold=0.5,
    max_refusal_count=3,
    safe_phrases=["feel free"],
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


def _lead(**kwargs) -> Lead:
    defaults = dict(
        id="test_lead_id",
        channel_user_id=99999,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return Lead(**defaults)


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

    def test_first_refusal_does_not_escalate(self):
        lead = _lead(refusal_count=0)
        verdict = check_safety(
            _output(reply_text="The price is $100"), RULES, lead,
        )
        assert not verdict.allowed
        assert not verdict.escalate
        assert lead.refusal_count == 1

    def test_refusal_at_limit_escalates_to_block(self):
        lead = _lead(refusal_count=2)
        verdict = check_safety(
            _output(reply_text="The price is $100"), RULES, lead,
        )
        assert not verdict.allowed
        assert verdict.escalate
        assert lead.refusal_count == 3

    def test_refusal_count_accumulates_across_messages(self):
        lead = _lead(refusal_count=0)
        check_safety(_output(reply_text="The price is $100"), RULES, lead)
        assert lead.refusal_count == 1
        verdict = check_safety(
            _output(reply_text="We guarantee results"), RULES, lead,
        )
        assert not verdict.allowed
        assert not verdict.escalate
        assert lead.refusal_count == 2

    def test_safety_without_lead_escalates_immediately(self):
        verdict = check_safety(
            _output(reply_text="The price is $100"), RULES, lead=None,
        )
        assert not verdict.allowed
        assert verdict.escalate

    def test_word_boundary_cure_does_not_match_curettage(self):
        verdict = check_safety(_output(reply_text="I need a curettage procedure"), RULES)
        assert verdict.allowed

    def test_word_boundary_cure_matches_standalone_cure(self):
        verdict = check_safety(_output(reply_text="Can you cure my tooth?"), RULES)
        assert not verdict.allowed

    def test_word_boundary_free_does_not_match_freelance(self):
        verdict = check_safety(_output(reply_text="I'm a freelance dentist"), RULES)
        assert verdict.allowed

    def test_word_boundary_free_matches_standalone_free(self):
        verdict = check_safety(_output(reply_text="Is this treatment free?"), RULES)
        assert not verdict.allowed


class TestSafePhrases:
    def test_feel_free_reply_allowed_and_refusal_count_unchanged(self):
        lead = _lead(refusal_count=0)
        verdict = check_safety(
            _output(reply_text="Feel free to ask us anything."),
            SAFE_PHRASES_RULES,
            lead,
        )
        assert verdict.allowed
        assert verdict.blocked_reason is None
        assert lead.refusal_count == 0

    def test_please_feel_free_reply_allowed(self):
        verdict = check_safety(
            _output(reply_text="Please feel free to share your phone number."),
            SAFE_PHRASES_RULES,
        )
        assert verdict.allowed

    @pytest.mark.parametrize(
        "reply_text",
        [
            "We offer a free consultation.",
            "It is free of charge.",
            "The price is 50.",
            "It will cost 50.",
            "We give a discount.",
            "We guarantee results.",
            "This will cure it.",
        ],
    )
    def test_blocked_phrases_still_blocked(self, reply_text):
        verdict = check_safety(_output(reply_text=reply_text), SAFE_PHRASES_RULES)
        assert not verdict.allowed

    def test_safe_phrase_does_not_whitelist_extracted_fields(self):
        output = _output(
            reply_text="Feel free to ask us anything.",
            extracted_fields=[
                ExtractedField(field_name="service", value="free consultation", confidence=0.8),
            ],
        )
        verdict = check_safety(output, SAFE_PHRASES_RULES)
        assert not verdict.allowed
        assert "free" in (verdict.blocked_reason or "")

    def test_old_rules_without_safe_phrases_unchanged(self):
        verdict = check_safety(
            _output(reply_text="Feel free to ask us anything."),
            RULES,
        )
        assert not verdict.allowed
        assert "free" in (verdict.blocked_reason or "")