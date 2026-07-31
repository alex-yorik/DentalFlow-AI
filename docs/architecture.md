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
├── channels/telegram/handlers.py — message_handler, handle_message (thin)
├── config/loader.py            — load_config() reads .env + client JSONs
├── followup/__init__.py         — FollowUpEngine, async polling loop
├── integrations/crm/provider.py — CRMProvider abstract base
├── integrations/crm/mock.py    — MockCRMProvider for development
├── leads/state_machine.py      — FiniteStateMachine with _TRANSITION_TABLE
├── leads/repository.py         — LeadRepository (CRUD on SQLite)
├── llm/client.py               — OpenAIClient, parse() with Pydantic model
├── llm/contracts.py            — AIOutput Pydantic model
├── rules/qualification.py      — score_lead() using configurable rules
├── rules/safety.py             — blocked_phrases check, refusal counter
├── rules/validator.py          — validate_ai_output(), validate_transition()
├── storage/database.py         — init_db(), get_db()
└── main.py                     — lifecycle: init → start → poll → shutdown
```

## Data Flow

```
User Message (Telegram)
  │
  ▼
src/channels/telegram/handlers.py (handle_message)
  │  1. Safety check — blocked phrases, refusal count, BLOCKED state
  │  2. Restore lead from DB, cancel follow-up if rejoining
  │  3. Build LLM context (state + known fields + conversation summary)
  │  4. Call LLM client — returns structured AIOutput (action, reply, fields)
  │  5. Validate output — validate_ai_output() checks safety + scope
  │  6. Extract fields — name, phone, service from LLM output
  │  7. State transition — suggest_state() + validate_transition() + apply_transition()
  │  8. Auto-advance — _try_advance_lead() if all critical fields collected
  ▼
src/integrations/crm/ (if state = crm_write)
  │  _write_to_crm() via CRMProvider interface
  │  Optionally schedule follow-up task
  ▼
src/storage/database.py
     Save lead, conversation summary, follow-up task
```

## Key Decisions Summary

- **Structured output only** — LLM returns a validated Pydantic model, not free text. Python validates before acting.
- **State machine for leads** — explicit transition table prevents illegal state changes.
- **CRM provider interface** — abstract base class with factory. Swap CRM via `DENTALFLOW_CRM_PROVIDER` env var.
- **Follow-up as async task** — background polling loop, no external scheduler. Tasks survive restarts (SQLite storage).
- **Conversation summaries** — 500-char structured summaries instead of raw transcripts. Saves space, protects PII.
- **Telegram is transport only** — handlers are thin; all business logic lives in `src/rules/`, `src/leads/`, `src/llm/`.