import asyncio
import logging
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.channels.web import adapter as web_adapter
from src.channels.whatsapp import adapter as wa_adapter
from src.entrypoints.web import _build_web_app
from src.leads.models import Lead
from src.llm.client import LLMClient
from src.llm.contracts import AIInput, AIOutput, Intent, SuggestedAction


def _make_lead(channel_user_id: int) -> Lead:
    now = datetime.now()
    return Lead(
        id=f"lead-{channel_user_id}",
        channel_user_id=channel_user_id,
        created_at=now,
        updated_at=now,
    )


def _output(text: str) -> AIOutput:
    return AIOutput(
        intent=Intent.FAQ,
        confidence=0.95,
        reply_text=text,
        is_lead=False,
        extracted_fields=[],
        missing_fields=[],
        suggested_action=SuggestedAction.ANSWER_FAQ,
        safe=True,
        crm_write_allowed=False,
        schedule_followup=False,
        escalation_needed=False,
        is_fallback=False,
    )


async def _echo_analyze(ai_input: AIInput) -> AIOutput:
    return _output(f"reply:{ai_input.user_message}")


@pytest.fixture
def mock_llm():
    client = MagicMock(spec=LLMClient)
    client.analyze = AsyncMock(side_effect=_echo_analyze)
    return client


@pytest.fixture
def app(demo_app_config, mock_llm, monkeypatch):
    async def fake_resolve_lead(chat_id, **kwargs):
        return _make_lead(chat_id), ""

    async def fake_process_message(msg, outgoing, lead, config, llm_client):
        output = await llm_client.analyze(
            AIInput(system_prompt="", user_message=msg.text)
        )
        await outgoing.send_message(msg.channel_user_id, output.reply_text)
        await asyncio.sleep(0.01)

    monkeypatch.setattr(web_adapter, "resolve_lead", fake_resolve_lead)
    monkeypatch.setattr(web_adapter, "process_message", fake_process_message)

    app = FastAPI()
    app.state.config = demo_app_config
    app.state.llm_client = mock_llm
    app.include_router(web_adapter.router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.mark.asyncio
async def test_same_channel_concurrent_requests_do_not_cross_talk(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        first, second = await asyncio.gather(
            ac.post("/api/chat", json={"channel_id": "shared", "text": "one"}),
            ac.post("/api/chat", json={"channel_id": "shared", "text": "two"}),
        )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["reply"] == "reply:one"
    assert second.json()["reply"] == "reply:two"


class TestChannelIsolation:
    def test_different_channel_ids_do_not_share_replies(self, client):
        first = client.post("/api/chat", json={"channel_id": "channel-a", "text": "alpha"})
        second = client.post("/api/chat", json={"channel_id": "channel-b", "text": "beta"})

        assert first.json()["reply"] == "reply:alpha"
        assert second.json()["reply"] == "reply:beta"

    def test_history_endpoint_removed(self, client):
        resp = client.get("/api/chat/user1/messages")
        assert resp.status_code in (404, 405)

    def test_no_module_level_response_store(self, client):
        for i in range(5):
            client.post("/api/chat", json={"channel_id": f"user-{i}", "text": "hi"})
        assert not hasattr(web_adapter, "_response_store")


class TestChatValidation:
    @pytest.mark.parametrize(
        "channel_id",
        ["bad id", "bad/id", "a" * 65, ""],
    )
    def test_invalid_channel_id_rejected(self, client, channel_id):
        resp = client.post("/api/chat", json={"channel_id": channel_id, "text": "hi"})
        assert resp.status_code == 422

    def test_text_over_limit_rejected(self, client):
        resp = client.post("/api/chat", json={"channel_id": "user1", "text": "x" * 2001})
        assert resp.status_code == 422

    def test_empty_text_rejected(self, client):
        resp = client.post("/api/chat", json={"channel_id": "user1", "text": ""})
        assert resp.status_code == 422


class TestCors:
    def test_no_cors_header_by_default(self, client):
        resp = client.options(
            "/api/chat",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert "access-control-allow-origin" not in resp.headers

    def test_configured_origins_allow_only_listed(self, demo_app_config, monkeypatch):
        monkeypatch.setattr("src.entrypoints.web.LLMClient", MagicMock)
        config = demo_app_config.model_copy(
            update={"cors_allow_origins": ["https://ok.example"]}
        )
        client = TestClient(_build_web_app(config))

        allowed = client.options(
            "/api/chat",
            headers={
                "Origin": "https://ok.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert allowed.headers["access-control-allow-origin"] == "https://ok.example"
        assert "access-control-allow-credentials" not in allowed.headers

        denied = client.options(
            "/api/chat",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert "access-control-allow-origin" not in denied.headers


class TestApiDocsDisabled:
    @pytest.fixture
    def built_client(self, demo_app_config, mock_llm, monkeypatch):
        async def fake_resolve_lead(chat_id, **kwargs):
            return _make_lead(chat_id), ""

        async def fake_process_message(msg, outgoing, lead, config, llm_client):
            output = await llm_client.analyze(
                AIInput(system_prompt="", user_message=msg.text)
            )
            await outgoing.send_message(msg.channel_user_id, output.reply_text)

        monkeypatch.setattr(web_adapter, "resolve_lead", fake_resolve_lead)
        monkeypatch.setattr(web_adapter, "process_message", fake_process_message)
        monkeypatch.setattr("src.entrypoints.web.LLMClient", MagicMock)
        app = _build_web_app(demo_app_config)
        app.state.llm_client = mock_llm
        return TestClient(app)

    @pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
    def test_api_docs_disabled(self, built_client, path):
        assert built_client.get(path).status_code == 404

    def test_health_still_available(self, built_client):
        resp = built_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_chat_still_works(self, built_client):
        resp = built_client.post(
            "/api/chat", json={"channel_id": "user1", "text": "hello"}
        )
        assert resp.status_code == 200
        assert resp.json()["reply"] == "reply:hello"


class TestWhatsAppVerificationHardening:
    @pytest.fixture
    def wa_app(self, demo_app_config):
        app = FastAPI()
        app.state.config = demo_app_config
        app.state.llm_client = MagicMock(spec=LLMClient)
        app.include_router(wa_adapter.router)
        return app

    @pytest.fixture
    def wa_client(self, wa_app):
        return TestClient(wa_app)

    @pytest.mark.parametrize("provided", ["accepted-secret", ""])
    def test_empty_token_rejects_every_request(
        self, wa_client, monkeypatch, caplog, provided
    ):
        monkeypatch.setattr(wa_adapter, "VERIFY_TOKEN", "")
        with caplog.at_level(logging.DEBUG):
            resp = wa_client.get(
                "/whatsapp/webhook",
                params={
                    "hub_mode": "subscribe",
                    "hub_verify_token": provided,
                    "hub_challenge": "abc123",
                },
            )

        assert resp.json() == {"error": "verification failed"}
        adapter_logs = "\n".join(
            record.getMessage()
            for record in caplog.records
            if record.name == wa_adapter.__name__
        )
        assert "accepted-secret" not in adapter_logs

    def test_no_module_level_response_store(self):
        assert not hasattr(wa_adapter, "_response_store")
