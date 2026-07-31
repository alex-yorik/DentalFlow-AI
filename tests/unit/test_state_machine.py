from datetime import datetime, timezone

import pytest

from src.leads.models import Lead, LeadState
from src.leads.state_machine import (
    suggest_state,
    validate_transition,
    apply_transition,
    ACTION_TO_STATE,
)
from src.llm.contracts import SuggestedAction
from src.config.loader import QualificationConfig


def _lead(state: LeadState = LeadState.NEW, **kwargs) -> Lead:
    now = datetime.now(timezone.utc)
    return Lead(
        id="test-id",
        telegram_chat_id=999,
        state=state,
        created_at=now,
        updated_at=now,
        **kwargs,
    )


QUAL_CONFIG = QualificationConfig(
    critical_fields=["name", "phone", "service_interest"],
    score_rules={
        "has_name": 10,
        "has_phone": 10,
        "has_email": 5,
        "has_service_interest": 10,
        "has_preferred_time": 5,
        "intent_is_new_appointment": 10,
        "urgency_is_urgent": 5,
    },
    crm_write_threshold=25,
)


class TestActionToStateMapping:
    def test_every_action_maps(self):
        for action in SuggestedAction:
            assert action in ACTION_TO_STATE

    def test_suggest_state_returns_valid_state(self):
        assert suggest_state(SuggestedAction.ANSWER_FAQ) == LeadState.FAQ_ONLY
        assert suggest_state(SuggestedAction.ASK_FIELD) == LeadState.COLLECT_FIELDS
        assert suggest_state(SuggestedAction.QUALIFY) == LeadState.QUALIFYING
        assert suggest_state(SuggestedAction.CRM_WRITE) == LeadState.CRM_WRITE
        assert suggest_state(SuggestedAction.CLOSE) == LeadState.CLOSED
        assert suggest_state(SuggestedAction.BLOCK) == LeadState.BLOCKED


class TestAllowedTransitions:
    def test_new_to_faq(self):
        result = validate_transition(LeadState.NEW, LeadState.FAQ_ONLY)
        assert result.allowed
        assert result.to_state == LeadState.FAQ_ONLY

    def test_new_to_collect(self):
        result = validate_transition(LeadState.NEW, LeadState.COLLECT_FIELDS)
        assert result.allowed

    def test_new_to_closed(self):
        result = validate_transition(LeadState.NEW, LeadState.CLOSED)
        assert result.allowed

    def test_new_to_blocked(self):
        result = validate_transition(LeadState.NEW, LeadState.BLOCKED)
        assert result.allowed

    def test_faq_to_collect(self):
        result = validate_transition(LeadState.FAQ_ONLY, LeadState.COLLECT_FIELDS)
        assert result.allowed

    def test_faq_to_closed(self):
        result = validate_transition(LeadState.FAQ_ONLY, LeadState.CLOSED)
        assert result.allowed

    def test_faq_to_blocked(self):
        result = validate_transition(LeadState.FAQ_ONLY, LeadState.BLOCKED)
        assert result.allowed

    def test_collect_to_qualifying_with_all_fields(self):
        lead = _lead(state=LeadState.COLLECT_FIELDS, name="John", phone="555-0100", service_interest="Cleaning")
        result = validate_transition(LeadState.COLLECT_FIELDS, LeadState.QUALIFYING, lead=lead, config=QUAL_CONFIG)
        assert result.allowed

    def test_collect_to_followup(self):
        result = validate_transition(LeadState.COLLECT_FIELDS, LeadState.FOLLOWUP_PENDING)
        assert result.allowed

    def test_collect_to_closed(self):
        result = validate_transition(LeadState.COLLECT_FIELDS, LeadState.CLOSED)
        assert result.allowed

    def test_collect_to_blocked(self):
        result = validate_transition(LeadState.COLLECT_FIELDS, LeadState.BLOCKED)
        assert result.allowed

    def test_qualifying_to_crm_write_with_sufficient_score(self):
        lead = _lead(
            state=LeadState.QUALIFYING,
            name="Jane", phone="555-0200", service_interest="Checkup",
            qualification_score=30,
        )
        result = validate_transition(LeadState.QUALIFYING, LeadState.CRM_WRITE, lead=lead, config=QUAL_CONFIG)
        assert result.allowed

    def test_qualifying_to_closed(self):
        result = validate_transition(LeadState.QUALIFYING, LeadState.CLOSED)
        assert result.allowed

    def test_qualifying_to_blocked(self):
        result = validate_transition(LeadState.QUALIFYING, LeadState.BLOCKED)
        assert result.allowed

    def test_crm_write_to_closed(self):
        result = validate_transition(LeadState.CRM_WRITE, LeadState.CLOSED)
        assert result.allowed

    def test_crm_write_to_blocked(self):
        result = validate_transition(LeadState.CRM_WRITE, LeadState.BLOCKED)
        assert result.allowed

    def test_crm_write_to_followup(self):
        result = validate_transition(LeadState.CRM_WRITE, LeadState.FOLLOWUP_PENDING)
        assert result.allowed

    def test_followup_to_collect(self):
        result = validate_transition(LeadState.FOLLOWUP_PENDING, LeadState.COLLECT_FIELDS)
        assert result.allowed

    def test_followup_to_closed(self):
        result = validate_transition(LeadState.FOLLOWUP_PENDING, LeadState.CLOSED)
        assert result.allowed

    def test_followup_to_blocked(self):
        result = validate_transition(LeadState.FOLLOWUP_PENDING, LeadState.BLOCKED)
        assert result.allowed

    def test_closed_to_blocked(self):
        result = validate_transition(LeadState.CLOSED, LeadState.BLOCKED)
        assert result.allowed


class TestDeniedTransitions:
    def test_collect_to_qualifying_missing_fields(self):
        lead = _lead(state=LeadState.COLLECT_FIELDS, name="John")  # missing phone, service_interest
        result = validate_transition(LeadState.COLLECT_FIELDS, LeadState.QUALIFYING, lead=lead, config=QUAL_CONFIG)
        assert not result.allowed
        assert "missing critical fields" in (result.reason or "")

    def test_qualifying_to_crm_write_below_threshold(self):
        lead = _lead(
            state=LeadState.QUALIFYING,
            name="John",  # has_name=10, but no phone and no service_interest
        )
        result = validate_transition(LeadState.QUALIFYING, LeadState.CRM_WRITE, lead=lead, config=QUAL_CONFIG)
        assert not result.allowed
        assert "score" in (result.reason or "").lower()

    def test_new_to_qualifying_skipping_collect(self):
        result = validate_transition(LeadState.NEW, LeadState.QUALIFYING)
        assert not result.allowed

    def test_new_to_crm_write(self):
        result = validate_transition(LeadState.NEW, LeadState.CRM_WRITE)
        assert not result.allowed

    def test_faq_to_qualifying(self):
        result = validate_transition(LeadState.FAQ_ONLY, LeadState.QUALIFYING)
        assert not result.allowed

    def test_faq_to_crm_write(self):
        result = validate_transition(LeadState.FAQ_ONLY, LeadState.CRM_WRITE)
        assert not result.allowed

    def test_closed_to_collect(self):
        result = validate_transition(LeadState.CLOSED, LeadState.COLLECT_FIELDS)
        assert not result.allowed

    def test_blocked_to_any(self):
        for state in LeadState:
            if state == LeadState.BLOCKED:
                continue
            result = validate_transition(LeadState.BLOCKED, state)
            assert not result.allowed, f"BLOCKED → {state.value} should be denied"

    def test_closed_to_qualifying(self):
        result = validate_transition(LeadState.CLOSED, LeadState.QUALIFYING)
        assert not result.allowed

    def test_closed_to_followup(self):
        result = validate_transition(LeadState.CLOSED, LeadState.FOLLOWUP_PENDING)
        assert not result.allowed


class TestApplyTransition:
    def test_apply_changes_state(self):
        lead = _lead(state=LeadState.NEW)
        apply_transition(lead, LeadState.FAQ_ONLY)
        assert lead.state == LeadState.FAQ_ONLY

    def test_apply_returns_updated_lead(self):
        lead = _lead(state=LeadState.NEW)
        updated = apply_transition(lead, LeadState.CLOSED)
        assert updated.state == LeadState.CLOSED
        assert updated is lead


class TestEdgeCases:
    def test_collect_to_qualifying_empty_lead(self):
        lead = _lead(state=LeadState.COLLECT_FIELDS)
        result = validate_transition(LeadState.COLLECT_FIELDS, LeadState.QUALIFYING, lead=lead, config=QUAL_CONFIG)
        assert not result.allowed

    def test_qualifying_to_crm_write_zero_score(self):
        lead = _lead(state=LeadState.QUALIFYING)
        result = validate_transition(LeadState.QUALIFYING, LeadState.CRM_WRITE, lead=lead, config=QUAL_CONFIG)
        assert not result.allowed

    def test_collect_to_qualifying_partial_fields(self):
        lead = _lead(
            state=LeadState.COLLECT_FIELDS,
            name="Alice", phone="555-0300",
        )
        result = validate_transition(LeadState.COLLECT_FIELDS, LeadState.QUALIFYING, lead=lead, config=QUAL_CONFIG)
        assert not result.allowed