import json
from pathlib import Path

import pytest

from src.config.loader import (
    ClientConfig,
    BusinessInfo,
    Service,
    FAQItem,
    RulesConfig,
    QualificationConfig,
    FollowUpConfig,
    load_client_config,
    CLIENTS_DIR,
)


class TestLoadClientConfig:
    def test_loads_demo_dental_successfully(self, demo_client_config: ClientConfig):
        assert isinstance(demo_client_config, ClientConfig)
        assert demo_client_config.business.name == "Bright Smile Dental"
        assert "welcome" in demo_client_config.business.messages
        assert len(demo_client_config.services) > 0
        assert len(demo_client_config.faq) > 0
        assert demo_client_config.rules.confidence_threshold == 0.5
        assert len(demo_client_config.qualification.critical_fields) == 3
        assert "initial" in demo_client_config.followup.templates

    def test_business_info_fields(self, demo_client_config: ClientConfig):
        biz = demo_client_config.business
        assert isinstance(biz, BusinessInfo)
        assert biz.address
        assert biz.phone
        assert biz.hours
        assert biz.timezone == "America/Chicago"
        assert biz.staff_chat_id == 0

    def test_services_have_required_fields(self, demo_client_config: ClientConfig):
        for svc in demo_client_config.services:
            assert isinstance(svc, Service)
            assert svc.name
            assert svc.description
            assert svc.duration_minutes > 0

    def test_faq_items_have_patterns_and_answers(self, demo_client_config: ClientConfig):
        for faq in demo_client_config.faq:
            assert isinstance(faq, FAQItem)
            assert len(faq.question_patterns) > 0
            assert faq.answer

    def test_rules_config(self, demo_client_config: ClientConfig):
        rules = demo_client_config.rules
        assert isinstance(rules, RulesConfig)
        assert len(rules.blocked_phrases) > 0
        assert rules.max_refusal_count > 0

    def test_qualification_config(self, demo_client_config: ClientConfig):
        qual = demo_client_config.qualification
        assert isinstance(qual, QualificationConfig)
        assert "has_name" in qual.score_rules
        assert qual.crm_write_threshold > 0

    def test_followup_config(self, demo_client_config: ClientConfig):
        fu = demo_client_config.followup
        assert isinstance(fu, FollowUpConfig)
        assert fu.poll_interval_seconds > 0
        assert fu.max_retries > 0

    def test_raises_on_missing_client(self):
        with pytest.raises(FileNotFoundError):
            load_client_config("nonexistent_client")

    def test_raises_on_malformed_json(self):
        bad_dir = CLIENTS_DIR / "__test_bad_json"
        bad_dir.mkdir(parents=True, exist_ok=True)
        (bad_dir / "business.json").write_text("{invalid json}")
        (bad_dir / "services.json").write_text("[]")
        (bad_dir / "faq.json").write_text("[]")
        (bad_dir / "rules.json").write_text("{}")
        (bad_dir / "qualification.json").write_text("{}")
        (bad_dir / "followup.json").write_text("{}")
        try:
            with pytest.raises(json.JSONDecodeError):
                load_client_config("__test_bad_json")
        finally:
            import shutil
            shutil.rmtree(bad_dir)


class TestAppConfig:
    def test_from_env_applies_defaults(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.setenv("OPENAI_API_KEY", "test_key")
        from src.config.loader import load_config
        cfg = load_config()
        assert cfg.telegram_bot_token == "test_token"
        assert cfg.openai_api_key == "test_key"
        assert cfg.client_name == "demo_dental"
        assert cfg.debug is False

    def test_debug_flag_from_env(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
        monkeypatch.setenv("OPENAI_API_KEY", "k")
        monkeypatch.setenv("DEBUG", "true")
        from src.config.loader import load_config
        assert load_config().debug is True