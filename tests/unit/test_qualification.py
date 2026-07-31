from datetime import datetime, timezone

from src.leads.models import Lead, LeadState
from src.config.loader import QualificationConfig
from src.rules.qualification import calculate_score


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


def _lead(**kwargs) -> Lead:
    now = datetime.now(timezone.utc)
    return Lead(
        id="test-id",
        telegram_chat_id=999,
        state=LeadState.COLLECT_FIELDS,
        created_at=now,
        updated_at=now,
        **kwargs,
    )


class TestQualification:
    def test_empty_lead_zero_score(self):
        result = calculate_score(_lead(), QUAL_CONFIG)
        assert result.score == 0
        assert not result.qualified
        assert result.breakdown == {}

    def test_name_only_partial(self):
        result = calculate_score(_lead(name="John"), QUAL_CONFIG)
        assert result.score == 10
        assert not result.qualified
        assert result.breakdown == {"has_name": 10}

    def test_name_and_phone(self):
        result = calculate_score(_lead(name="John", phone="555-0100"), QUAL_CONFIG)
        assert result.score == 20
        assert not result.qualified

    def test_all_critical_fields_meets_threshold(self):
        result = calculate_score(
            _lead(name="John", phone="555-0100", service_interest="Cleaning"),
            QUAL_CONFIG,
        )
        assert result.score == 30
        assert result.qualified

    def test_all_fields_max_score(self):
        result = calculate_score(
            _lead(
                name="John", phone="555-0100", email="john@test.com",
                service_interest="Checkup", preferred_time="10:00",
                intent="new_appointment", urgency="urgent",
            ),
            QUAL_CONFIG,
        )
        assert result.score == 55
        assert result.qualified

    def test_breakdown_contains_all_contributing_rules(self):
        result = calculate_score(
            _lead(name="John", phone="555-0100", service_interest="Cleaning"),
            QUAL_CONFIG,
        )
        assert set(result.breakdown.keys()) == {"has_name", "has_phone", "has_service_interest"}

    def test_email_and_preferred_time_boost_not_required(self):
        result = calculate_score(
            _lead(name="John", phone="555-0100", email="j@t.com", preferred_time="09:00"),
            QUAL_CONFIG,
        )
        assert result.score == 30
        assert result.qualified

    def test_urgency_not_urgent_no_boost(self):
        result = calculate_score(
            _lead(name="John", phone="555-0100", service_interest="Cleaning", urgency="normal"),
            QUAL_CONFIG,
        )
        assert result.score == 30

    def test_urgent_boost_applied(self):
        result = calculate_score(
            _lead(name="John", phone="555-0100", service_interest="Cleaning", urgency="urgent"),
            QUAL_CONFIG,
        )
        assert result.score == 35

    def test_intent_new_appointment_boost(self):
        result = calculate_score(
            _lead(name="John", phone="555-0100", service_interest="Cleaning", intent="new_appointment"),
            QUAL_CONFIG,
        )
        assert result.score == 40


class TestQualificationEdgeCases:
    def test_empty_strings_not_counted(self):
        result = calculate_score(_lead(name="", phone="", service_interest=""), QUAL_CONFIG)
        assert result.score == 0
        assert not result.qualified

    def test_whitespace_only_not_counted(self):
        result = calculate_score(_lead(name="   ", phone="555-0100"), QUAL_CONFIG)
        assert result.score == 10
        assert "has_name" not in result.breakdown

    def test_different_threshold(self):
        low_config = QualificationConfig(
            critical_fields=["name"],
            score_rules={"has_name": 5},
            crm_write_threshold=3,
        )
        result = calculate_score(_lead(name="John"), low_config)
        assert result.qualified

    def test_high_threshold_not_met(self):
        high_config = QualificationConfig(
            critical_fields=["name", "phone", "email", "service_interest"],
            score_rules={"has_name": 10, "has_phone": 10, "has_email": 5, "has_service_interest": 10},
            crm_write_threshold=50,
        )
        result = calculate_score(
            _lead(name="John", phone="555-0100", service_interest="Cleaning"),
            high_config,
        )
        assert result.score == 30
        assert not result.qualified