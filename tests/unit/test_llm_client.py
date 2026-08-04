from unittest.mock import AsyncMock, patch

import pytest

from src.llm.client import LLMClient
from src.llm.contracts import AIInput, AIOutput


def _make_mock_response(output: AIOutput) -> AsyncMock:
    mock_message = AsyncMock()
    mock_message.parsed = output
    mock_choice = AsyncMock()
    mock_choice.message = mock_message
    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]
    return mock_response


class TestLLMClient:
    def test_constructor(self):
        client = LLMClient(api_key="test_key", model="gpt-4o-mini")
        assert client.model == "gpt-4o-mini"

    def test_constructor_passes_base_url_to_sdk(self):
        with patch("src.llm.client.AsyncOpenAI") as mock_openai:
            LLMClient(api_key="test_key", base_url="https://openrouter.ai/api/v1")
        mock_openai.assert_called_once_with(api_key="test_key", base_url="https://openrouter.ai/api/v1")

    def test_constructor_without_base_url_keeps_previous_behavior(self):
        with patch("src.llm.client.AsyncOpenAI") as mock_openai:
            LLMClient(api_key="test_key")
        mock_openai.assert_called_once_with(api_key="test_key")

    def test_config_base_url_wired_into_client(self):
        from src.bootstrap import bootstrap
        with patch("src.bootstrap.load_config") as mock_load, patch("src.bootstrap.LLMClient") as mock_client, patch("src.bootstrap.validate_required_env"), patch("src.bootstrap.setup_logging"):
            from unittest.mock import MagicMock
            cfg = MagicMock()
            cfg.openai_api_key = "k"
            cfg.openai_model = "gpt-4o-mini"
            cfg.base_url = "https://openrouter.ai/api/v1"
            mock_load.return_value = cfg
            bootstrap()
        mock_client.assert_called_once_with(api_key="k", model="gpt-4o-mini", base_url="https://openrouter.ai/api/v1")

    async def test_analyze_returns_parsed_output(self):
        expected = AIOutput(
            intent="faq",
            confidence=0.95,
            reply_text="We are open Mon-Fri.",
            is_lead=False,
            extracted_fields=[],
            missing_fields=[],
            suggested_action="answer_faq",
            safe=True,
            crm_write_allowed=False,
            schedule_followup=False,
            escalation_needed=False,
        )
        mock_client = AsyncMock()
        mock_client.beta.chat.completions.parse = AsyncMock(
            return_value=_make_mock_response(expected)
        )

        client = LLMClient(client=mock_client)
        result = await client.analyze(
            AIInput(system_prompt="You are a helper", user_message="What are your hours?")
        )

        assert result.intent == "faq"
        assert result.reply_text == "We are open Mon-Fri."

    async def test_analyze_with_conversation_context(self):
        mock_client = AsyncMock()
        mock_client.beta.chat.completions.parse = AsyncMock(
            return_value=_make_mock_response(
                AIOutput(
                    intent="lead",
                    confidence=0.85,
                    reply_text="I'd like to help you book.",
                    is_lead=True,
                    extracted_fields=[{"field_name": "name", "value": "John", "confidence": 0.95}],
                    missing_fields=["phone", "service_interest"],
                    suggested_action="ask_field",
                    safe=True,
                    crm_write_allowed=False,
                    schedule_followup=False,
                    escalation_needed=False,
                )
            )
        )

        client = LLMClient(client=mock_client)
        result = await client.analyze(
            AIInput(
                system_prompt="You are a receptionist",
                user_message="My name is John",
                conversation_context="State: COLLECT_FIELDS. Known: none",
            )
        )

        assert result.intent == "lead"
        assert result.is_lead is True
        assert len(result.extracted_fields) == 1

    async def test_fallback_on_api_error(self):
        mock_client = AsyncMock()
        mock_client.beta.chat.completions.parse = AsyncMock(
            side_effect=Exception("API timeout")
        )

        client = LLMClient(client=mock_client)
        result = await client.analyze(
            AIInput(system_prompt="You are a helper", user_message="Hi")
        )

        assert result.intent == "off_topic"
        assert result.confidence == 0.0
        assert result.escalation_needed is True
        assert "API error" in (result.escalation_reason or "")
        assert result.is_fallback is True

    async def test_fallback_on_null_parsed(self):
        mock_message = AsyncMock()
        mock_message.parsed = None
        mock_choice = AsyncMock()
        mock_choice.message = mock_message
        mock_response = AsyncMock()
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_response)

        client = LLMClient(client=mock_client)
        result = await client.analyze(
            AIInput(system_prompt="You are a helper", user_message="Hi")
        )

        assert result.intent == "off_topic"
        assert result.escalation_needed is True
        assert "null" in (result.escalation_reason or "")
        assert result.is_fallback is True

    async def test_passes_messages_to_api(self):
        mock_parse = AsyncMock(return_value=_make_mock_response(
            AIOutput(
                intent="faq", confidence=0.9, reply_text="Yes",
                is_lead=False, extracted_fields=[], missing_fields=[],
                suggested_action="answer_faq", safe=True,
                crm_write_allowed=False, schedule_followup=False,
                escalation_needed=False,
            )
        ))
        mock_client = AsyncMock()
        mock_client.beta.chat.completions.parse = mock_parse

        client = LLMClient(client=mock_client)
        await client.analyze(
            AIInput(system_prompt="Be helpful", user_message="Hello")
        )

        mock_parse.assert_called_once()
        _, kwargs = mock_parse.call_args
        messages = kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "Be helpful"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"