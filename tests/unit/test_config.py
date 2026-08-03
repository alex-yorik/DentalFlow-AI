import pytest

from src.config.loader import REQUIRED_ENV_VARS, load_config, validate_required_env


class TestValidateRequiredEnv:
    def test_raises_when_token_missing(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "key")
        with pytest.raises(ValueError) as exc:
            validate_required_env()
        assert "TELEGRAM_BOT_TOKEN" in str(exc.value)

    def test_raises_when_api_key_missing(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError) as exc:
            validate_required_env()
        assert "OPENAI_API_KEY" in str(exc.value)

    def test_raises_when_both_missing(self, monkeypatch):
        for var in REQUIRED_ENV_VARS:
            monkeypatch.delenv(var, raising=False)
        with pytest.raises(ValueError) as exc:
            validate_required_env()
        assert "TELEGRAM_BOT_TOKEN" in str(exc.value)
        assert "OPENAI_API_KEY" in str(exc.value)

    def test_raises_on_blank_token(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "   ")
        monkeypatch.setenv("OPENAI_API_KEY", "key")
        with pytest.raises(ValueError):
            validate_required_env()

    def test_passes_when_all_present(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
        monkeypatch.setenv("OPENAI_API_KEY", "key")
        validate_required_env()


class TestLoadConfigValidation:
    def test_load_config_raises_when_token_missing(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "key")
        with pytest.raises(ValueError):
            load_config()

    def test_load_config_succeeds_with_all_required(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
        monkeypatch.setenv("OPENAI_API_KEY", "key")
        cfg = load_config()
        assert cfg.telegram_bot_token == "token"
        assert cfg.openai_api_key == "key"
