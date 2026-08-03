import pytest

from src.config.loader import AppConfig, MonitoringConfig, load_client_config
from src.monitoring.alerter import Alerter

_CLIENT = load_client_config("demo_dental")


def _cfg(chat_id=None) -> AppConfig:
    return AppConfig(
        telegram_bot_token="t",
        openai_api_key="k",
        client_name="demo_dental",
        client=_CLIENT,
        monitoring=MonitoringConfig(alerts_chat_id=chat_id),
    )


class FakeBot:
    def __init__(self):
        self.sent = []

    async def send_message(self, chat_id, text, parse_mode=None):
        self.sent.append({"chat_id": chat_id, "text": text, "parse_mode": parse_mode})


@pytest.mark.asyncio
async def test_send_down():
    bot = FakeBot()
    await Alerter(_cfg(chat_id=123), bot).send_down("web")
    assert len(bot.sent) == 1
    assert "DOWN" in bot.sent[0]["text"]
    assert bot.sent[0]["chat_id"] == 123


@pytest.mark.asyncio
async def test_send_recovered():
    bot = FakeBot()
    await Alerter(_cfg(chat_id=123), bot).send_recovered("telegram")
    assert "RECOVERED" in bot.sent[0]["text"]


@pytest.mark.asyncio
async def test_skips_when_no_chat_id():
    bot = FakeBot()
    await Alerter(_cfg(chat_id=None), bot).send_down("web")
    assert bot.sent == []


@pytest.mark.asyncio
async def test_handles_bot_error(monkeypatch):
    class ErrorBot(FakeBot):
        async def send_message(self, chat_id, text, parse_mode=None):
            raise RuntimeError("boom")

    await Alerter(_cfg(chat_id=123), ErrorBot()).send_down("web")
