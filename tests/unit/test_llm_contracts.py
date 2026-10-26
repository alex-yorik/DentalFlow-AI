import pytest
from pydantic import ValidationError

from src.llm.contracts import AIInput, AIOutput, ExtractedField, Intent, SuggestedAction


class TestExtractedField:
    def test_valid_field(self):
        f = ExtractedField(field_name="name", value="John", confidence=0.95)
        assert f.field_name == "name"
        assert f.value == "John"
        assert f.confidence == 0.95

    def test_confidence_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            ExtractedField(field_name="name", value="John", confidence=1.5)

    def test_negative_confidence_raises(self):
        with pytest.raises(ValidationError):
            ExtractedField(field_name="name", value="John", confidence=-0.1)


class TestAIOutput:
    def test_valid_output(self):
        output = AIOutput(
            intent=Intent.FAQ,
            confidence=0.95,
            reply_text="We are open Mon-Fri.",
            is_lead=False,
            extracted_fields=[ExtractedField(field_name="service", value="Cleaning", confidence=0.8)],
            missing_fields=[],
            suggested_action=SuggestedAction.ANSWER_FAQ,
            safe=True,
            crm_write_allowed=False,
            schedule_followup=False,
            escalation_needed=False,
        )
        assert output.intent == Intent.FAQ
        assert output.confidence == 0.95
        assert len(output.extracted_fields) == 1

    def test_minimal_output(self):
        output = AIOutput(
            intent=Intent.FAQ,
            confidence=0.5,
            reply_text="Hello",
            is_lead=False,
            extracted_fields=[],
            missing_fields=[],
            suggested_action=SuggestedAction.CLOSE,
            safe=True,
            crm_write_allowed=False,
            schedule_followup=False,
            escalation_needed=False,
        )
        assert output.intent == Intent.FAQ

    def test_invalid_intent_raises(self):
        with pytest.raises(ValidationError):
            AIOutput(
                intent="invalid_intent",
                confidence=0.5,
                reply_text="Hi",
                is_lead=False,
                extracted_fields=[],
                missing_fields=[],
                suggested_action=SuggestedAction.CLOSE,
                safe=True,
                crm_write_allowed=False,
                schedule_followup=False,
                escalation_needed=False,
            )

    def test_invalid_suggested_action_raises(self):
        with pytest.raises(ValidationError):
            AIOutput(
                intent=Intent.FAQ,
                confidence=0.5,
                reply_text="Hi",
                is_lead=False,
                extracted_fields=[],
                missing_fields=[],
                suggested_action="do_something_else",
                safe=True,
                crm_write_allowed=False,
                schedule_followup=False,
                escalation_needed=False,
            )

    def test_escalation_reason_optional(self):
        output = AIOutput(
            intent=Intent.OFF_TOPIC,
            confidence=0.3,
            reply_text="I don't understand",
            is_lead=False,
            extracted_fields=[],
            missing_fields=[],
            suggested_action=SuggestedAction.CLOSE,
            safe=True,
            crm_write_allowed=False,
            schedule_followup=False,
            escalation_needed=True,
            escalation_reason="Low confidence",
        )
        assert output.escalation_reason == "Low confidence"

    def test_from_json(self):
        json_str = '''{
            "intent": "lead",
            "confidence": 0.9,
            "reply_text": "We'd love to help!",
            "is_lead": true,
            "extracted_fields": [
                {"field_name": "name", "value": "Jane", "confidence": 0.99}
            ],
            "missing_fields": ["phone", "service_interest"],
            "suggested_action": "ask_field",
            "safe": true,
            "crm_write_allowed": false,
            "schedule_followup": false,
            "escalation_needed": false
        }'''
        output = AIOutput.model_validate_json(json_str)
        assert output.intent == Intent.LEAD
        assert output.is_lead is True
        assert len(output.extracted_fields) == 1
        assert output.extracted_fields[0].value == "Jane"

    def test_from_json_missing_fields_raises(self):
        with pytest.raises(ValidationError):
            AIOutput.model_validate_json('{"intent": "faq"}')

    def test_from_json_none_confidence_raises(self):
        with pytest.raises(ValidationError):
            AIOutput.model_validate_json('''{
                "intent": "faq",
                "confidence": null,
                "reply_text": "Hi",
                "is_lead": false,
                "extracted_fields": [],
                "missing_fields": [],
                "suggested_action": "close",
                "safe": true,
                "crm_write_allowed": false,
                "schedule_followup": false,
                "escalation_needed": false
            }''')


class TestAIInput:
    def test_valid_input(self):
        inp = AIInput(
            system_prompt="You are a receptionist",
            user_message="Hi there",
        )
        assert inp.system_prompt == "You are a receptionist"
        assert inp.user_message == "Hi there"
        assert inp.conversation_context == ""

    def test_with_context(self):
        inp = AIInput(
            system_prompt="You are a receptionist",
            user_message="I want to book",
            conversation_context="State: COLLECT_FIELDS. Known: name=John",
        )
        assert inp.conversation_context == "State: COLLECT_FIELDS. Known: name=John"
