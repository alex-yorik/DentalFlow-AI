from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.channels.whatsapp.adapter import (
    WhatsAppOutgoingAdapter,
    router,
)
from src.llm.client import LLMClient


@pytest.fixture
def app(demo_app_config):
    app = FastAPI()
    app.state.config = demo_app_config
    app.state.llm_client = MagicMock(spec=LLMClient)
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestWhatsAppOutgoingAdapter:
    def test_send_message_stores_with_phone(self):
        import asyncio

        adapter = WhatsAppOutgoingAdapter("+79160000000")
        asyncio.run(adapter.send_message("+79160000000", "hello"))
        assert adapter.sent == ["hello"]

    def test_send_message_falls_back_to_own_phone(self):
        import asyncio

        adapter = WhatsAppOutgoingAdapter("+79160000001")
        asyncio.run(adapter.send_message("", "hi"))
        assert adapter.sent == ["hi"]


class TestWhatsAppVerify:
    def test_verify_success(self, client, monkeypatch):
        from src.channels.whatsapp import adapter as wa

        monkeypatch.setattr(wa, "VERIFY_TOKEN", "expected-token")
        resp = client.get(
            "/whatsapp/webhook",
            params={"hub_mode": "subscribe", "hub_verify_token": "expected-token", "hub_challenge": "abc123"},
        )
        assert resp.status_code == 200
        assert resp.json() == "abc123"

    def test_verify_failure(self, client, monkeypatch):
        from src.channels.whatsapp import adapter as wa

        monkeypatch.setattr(wa, "VERIFY_TOKEN", "expected-token")
        resp = client.get(
            "/whatsapp/webhook",
            params={"hub_mode": "subscribe", "hub_verify_token": "wrong", "hub_challenge": "abc123"},
        )
        assert resp.status_code == 200
        assert resp.json() == {"error": "verification failed"}


class TestWhatsAppWebhook:
    def test_creates_lead_and_returns_reply(self, client, monkeypatch):
        from src.channels.whatsapp import adapter as wa

        created = []

        async def fake_get_lead(*args, **kwargs):
            return None

        async def fake_create_lead(chat_id, source="", channel_type=""):
            created.append((chat_id, source, channel_type))
            return None

        monkeypatch.setattr("src.core.lead_lookup.get_lead_by_chat_id", fake_get_lead)
        monkeypatch.setattr("src.core.lead_lookup.create_lead", fake_create_lead)

        async def fake_process_message(msg, outgoing, lead, config, llm_client):
            await outgoing.send_message(msg.channel_user_id, "Bonjour")

        monkeypatch.setattr(wa, "process_message", fake_process_message)

        resp = client.post("/whatsapp/webhook", json={"phone_number": "+79160000002", "text": "hello"})
        assert resp.status_code == 200
        assert resp.json()["reply"] == "Bonjour"
        assert created and created[0][1] == "whatsapp" and created[0][2] == "whatsapp"

    def test_blocked_lead_returns_error(self, client, monkeypatch, demo_app_config):
        from datetime import datetime

        from src.leads.models import Lead, LeadState

        now = datetime.now()
        blocked = Lead(id="b1", channel_user_id=123, state=LeadState.BLOCKED, created_at=now, updated_at=now)
        monkeypatch.setattr("src.core.lead_lookup.get_lead_by_chat_id", AsyncMock(return_value=blocked))

        resp = client.post("/whatsapp/webhook", json={"phone_number": "+79160000003", "text": "hi"})
        expected = demo_app_config.client.business.messages.get("error_unsafe", "")
        assert resp.status_code == 200
        assert resp.json()["reply"] == expected
