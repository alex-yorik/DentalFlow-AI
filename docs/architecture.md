# Architecture

## System Boundaries

DentalFlow AI separates six core domains:

| Domain | Boundary | Responsibility |
|--------|----------|---------------|
| **Channels** | `src/channels/` | Transport-layer handlers. Parse incoming messages, delegate to core, format responses. |
| **AI Layer** | `src/llm/` | OpenAI client. Sends prompts with context, receives structured Pydantic output only. |
| **Business Rules** | `src/rules/` | Safety validation, FAQ routing, out-of-scope detection. Pure Python, no LLM. |
| **Leads** | `src/leads/` | State machine, qualification scoring, lead repository. All state transitions go through `validate_transition()`. |
| **Storage** | `src/storage/` | SQLite via aiosqlite. Conversation summaries, lead data, follow-up tasks. |
| **Integrations** | `src/integrations/` | CRM provider interface (`CRMProvider` base class). Factory pattern, provider selected by env var. |

## Module Responsibilities

```
src/
├── channels/telegram/bot.py    — create_bot(), handler registration
├── channels/telegram/handlers/ — message_handler, callback_handler (thin)
├── config/loader.py            — load_config() reads .env + client JSONs
├── followup/engine.py          — FollowUpEngine, async polling loop
├── integrations/crm/base.py    — CRMProvider abstract base
├── integrations/crm/mock.py    — MockCRMProvider for development
├── leads/state_machine.py      — FiniteStateMachine with _TRANSITION_TABLE
├── leads/qualification.py      — score_lead() using configurable rules
├── leads/repository.py         — LeadRepository (CRUD on SQLite)
├── llm/client.py               — OpenAIClient, parse() with Pydantic model
├── llm/contracts.py            — AIOutput Pydantic model
├── rules/safety.py             — blocked_phrases check, refusal counter
├── rules/validator.py          — validate_safe_action(), validate_transition()
├── rules/faq.py                — FAQ matching from client config
├── storage/database.py         — init_db(), get_db()
└── main.py                     — lifecycle: init → start → poll → shutdown
```

## Data Flow

```
User Message (Telegram)
  │
  ▼
src/channels/telegram/handlers/
  │  parse update → extract chat_id, text
  │  call process_message(chat_id, text)
  ▼
src/leads/handler.py
  │  1. Safety check (blocked phrases, refusal count)
  │  2. FAQ match → respond directly
  │  3. Build LLM context (config + conversation summary)
  ▼
src/llm/client.py → OpenAI API
  │  Returns structured AIOutput (action, reply, fields...)
  ▼
src/rules/validator.py
  │  Validate action: is it safe? Is the transition legal?
  ▼
src/leads/state_machine.py
  │  validate_transition() + apply_transition()
  ▼
src/storage/database.py
  │  Save lead, conversation summary, follow-up task
  ▼
src/integrations/crm/ (if threshold met)
     Write lead to CRM provider
```

## Key Decisions Summary

- **Structured output only** — LLM returns a validated Pydantic model, not free text. Python validates before acting.
- **State machine for leads** — explicit transition table prevents illegal state changes.
- **CRM provider interface** — abstract base class with factory. Swap CRM via `DENTALFLOW_CRM_PROVIDER` env var.
- **Follow-up as async task** — background polling loop, no external scheduler. Tasks survive restarts (SQLite storage).
- **Conversation summaries** — 500-char structured summaries instead of raw transcripts. Saves space, protects PII.
- **Telegram is transport only** — handlers are thin; all business logic lives in `src/rules/`, `src/leads/`, `src/llm/`.