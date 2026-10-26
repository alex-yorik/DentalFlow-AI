from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.channels.web.adapter import router
from src.leads.models import Lead
from src.llm.contracts import AIOutput, Intent, SuggestedAction
from src.llm.client import LLMClient


def _make_lead(**overrides) -> Lead:
    now = datetime.now()
    defaults = dict(
        id="test-id",
        channel_user_id=0,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return Lead(**defaults)


@pytest.fixture
def mock_llm():
    client = MagicMock(spec=LLMClient)
    client.analyze = AsyncMock()
    return client


@pytest.fixture
def app(demo_app_config, mock_llm):
    app = FastAPI()
    app.state.config = demo_app_config
    app.state.llm_client = mock_llm
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestChatEndpoint:
    def test_reply_success(self, client, mock_llm, monkeypatch):
        mock_llm.analyze.return_value = AIOutput(
            intent=Intent.FAQ,
            confidence=0.95,
            reply_text="We are open Mon-Fri 8-5.",
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

        async def fake_get_lead(*args, **kwargs):
            return None

        async def fake_create_lead(*args, **kwargs):
            return _make_lead(
                channel_user_id=hash("test_channel") & 0x7FFFFFFF,
                source="web",
                channel_type="web",
            )

        monkeypatch.setattr("src.core.lead_lookup.get_lead_by_chat_id", fake_get_lead)
        monkeypatch.setattr("src.core.lead_lookup.create_lead", fake_create_lead)

        resp = client.post("/api/chat", json={"channel_id": "test_channel", "text": "What are your hours?"})
        assert resp.status_code == 200
        data = resp.json()
        assert "reply" in data
        assert data["reply"] == "We are open Mon-Fri 8-5."

    def test_blocked_lead_gets_error_message(self, client, monkeypatch, demo_app_config):
        from src.leads.models import LeadState

        blocked_lead = _make_lead(
            channel_user_id=12345,
            state=LeadState.BLOCKED,
            source="web",
            channel_type="web",
        )

        async def fake_get_lead(*args, **kwargs):
            return blocked_lead

        monkeypatch.setattr("src.core.lead_lookup.get_lead_by_chat_id", fake_get_lead)

        resp = client.post("/api/chat", json={"channel_id": "blocked_user", "text": "Hello"})
        assert resp.status_code == 200
        data = resp.json()
        expected = demo_app_config.client.business.messages.get("error_unsafe", "")
        assert data["reply"] == expected

    def test_closed_lead_resets_and_creates_new(self, client, mock_llm, monkeypatch):
        from src.leads.models import LeadState

        closed_lead = _make_lead(
            channel_user_id=12345,
            state=LeadState.CLOSED,
            source="web",
            channel_type="web",
        )

        mock_llm.analyze.return_value = AIOutput(
            intent=Intent.FAQ,
            confidence=0.95,
            reply_text="Welcome back!",
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

        call_count = 0

        async def fake_get_lead(*args, **kwargs):
            return closed_lead

        async def fake_create_lead(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return _make_lead(
                channel_user_id=hash("returning_user") & 0x7FFFFFFF,
                source="web",
                channel_type="web",
            )

        monkeypatch.setattr("src.core.lead_lookup.get_lead_by_chat_id", fake_get_lead)
        monkeypatch.setattr("src.core.lead_lookup.create_lead", fake_create_lead)

        resp = client.post("/api/chat", json={"channel_id": "returning_user", "text": "I'm back"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["reply"] == "Welcome back!"
        assert call_count == 1

    def test_create_lead_with_web_source(self, client, mock_llm, monkeypatch):
        mock_llm.analyze.return_value = AIOutput(
            intent=Intent.FAQ,
            confidence=0.95,
            reply_text="Hello!",
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

        created_leads = []

        async def fake_get_lead(*args, **kwargs):
            return None

        async def fake_create_lead(chat_id, source="", channel_type=""):
            lead = _make_lead(
                channel_user_id=chat_id,
                source=source,
                channel_type=channel_type,
            )
            created_leads.append(lead)
            return lead

        monkeypatch.setattr("src.core.lead_lookup.get_lead_by_chat_id", fake_get_lead)
        monkeypatch.setattr("src.core.lead_lookup.create_lead", fake_create_lead)

        resp = client.post("/api/chat", json={"channel_id": "new_user", "text": "Hi"})
        assert resp.status_code == 200
        assert len(created_leads) == 1
        assert created_leads[0].source == "web"
        assert created_leads[0].channel_type == "web"

    def test_returns_error_for_missing_text(self, client):
        resp = client.post("/api/chat", json={"channel_id": "test"})
        assert resp.status_code == 422


class TestChatPage:
    def test_returns_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "DentalFlow AI Chat" in resp.text