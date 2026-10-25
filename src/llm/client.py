import logging
from typing import Any, cast

from openai import AsyncOpenAI

from src.llm.contracts import AIInput, AIOutput, Intent, SuggestedAction

logger = logging.getLogger(__name__)

_FALLBACK_REPLY = "I'm sorry, I couldn't process your request. Please try again or contact us by phone."


class LLMClient:
    def __init__(
        self,
        *,
        api_key: str = "",
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        client: AsyncOpenAI | None = None,
    ):
        self.model = model
        if client is not None:
            self._client = client
        elif base_url is not None:
            self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        else:
            self._client = AsyncOpenAI(api_key=api_key)

    async def analyze(self, input_data: AIInput) -> AIOutput:
        messages = [
            {"role": "system", "content": input_data.system_prompt},
        ]
        if input_data.conversation_context:
            messages.append({"role": "system", "content": f"Conversation context:\n{input_data.conversation_context}"})
        for dm in input_data.recent_messages:
            role = "assistant" if dm.role == "assistant" else "user"
            messages.append({"role": role, "content": dm.text})
        messages.append({"role": "user", "content": input_data.user_message})

        try:
            response = await self._client.beta.chat.completions.parse(
                model=self.model,
                messages=cast(Any, messages),
                response_format=AIOutput,
                temperature=0.1,
            )
        except Exception as e:
            logger.error("OpenAI API call failed: %s", e)
            return self._fallback(reason=f"API error: {e}")

        parsed = response.choices[0].message.parsed
        if parsed is None:
            logger.error("Model returned null parsed response")
            return self._fallback(reason="Model returned null")

        return parsed

    def _fallback(self, reason: str) -> AIOutput:
        return AIOutput(
            intent=Intent.OFF_TOPIC,
            confidence=0.0,
            reply_text=_FALLBACK_REPLY,
            is_lead=False,
            extracted_fields=[],
            missing_fields=[],
            suggested_action=SuggestedAction.CLOSE,
            safe=True,
            crm_write_allowed=False,
            schedule_followup=False,
            escalation_needed=True,
            escalation_reason=reason,
            is_fallback=True,
        )