# Architecture Decisions

This file records all significant architecture decisions made during the project.
Each entry follows the same template.

---

## Decision 001 — Structured LLM Output Only

**Date:** Phase 2

**Problem:** The LLM might return unstructured text, making it impossible for Python to validate actions before execution.

**Alternatives:**
- Let the LLM return free text and parse it with regex/NLP
- Use function calling (OpenAI tool use)
- Use structured output (Pydantic `parse()`)

**Chosen Solution:** Use OpenAI structured output API (`client.beta.chat.completions.parse()`) with a Pydantic model (`AIOutput`).

**Reason:** Python needs to validate every critical action before it happens. Structured output guarantees a parseable schema. No regex, no hallucinated field names.

**Trade-offs:** Requires Pydantic v2 and the `parse()` beta API. Falls back to a safe default if the API fails.

**Status:** ACTIVE

---

## Decision 002 — State Machine for Leads

**Date:** Phase 3

**Problem:** Lead handling can follow many paths (FAQ, collection, qualification, CRM write, follow-up). Without a state machine, transitions become implicit and bugs appear.

**Alternatives:**
- Free-form state management with if/else chains
- Finite state machine with explicit transition table

**Chosen Solution:** Finite state machine with an explicit `_TRANSITION_TABLE` dict mapping `(from, to) → reason`. All transitions go through `validate_transition()` before `apply_transition()`.

**Reason:** Explicit transitions prevent illegal state changes. The table is readable, testable, and extendable.

**Trade-offs:** Every new state requires a table entry. Some transitions need runtime checks (e.g., qualification score threshold).

**Status:** ACTIVE

---

## Decision 003 — CRM Provider Interface

**Date:** Phase 5

**Problem:** The project must support multiple CRM backends (mock, HubSpot, Salesforce) without changing lead-handling code.

**Alternatives:**
- Direct CRM API calls in handlers
- Abstract provider interface with a registry

**Chosen Solution:** Abstract `CRMProvider` base class with a `get_provider()` factory. The provider name comes from the environment variable `DENTALFLOW_CRM_PROVIDER`.

**Reason:** Handlers never call CRM APIs directly. Swapping providers is a config change, not a code change.

**Trade-offs:** Adds interface overhead. Only the mock provider is implemented so far.

**Status:** ACTIVE

---

## Decision 004 — Telegram as Transport Only

**Date:** Phase 4

**Problem:** Business logic risks leaking into Telegram handlers, making the system hard to port to web or WhatsApp.

**Alternatives:**
- Put business logic in handlers
- Keep handlers thin and delegate to `src/rules/`, `src/leads/`, etc.

**Chosen Solution:** Handlers only parse the update and call into `src/rules/`, `src/leads/`, `src/llm/`. No business decisions in handlers.

**Reason:** Web and WhatsApp channels will reuse the same core. Handler code is minimal and channel-specific.

**Trade-offs:** Requires more files and more imports. Clearer separation.

**Status:** ACTIVE

---

## Decision 005 — Follow-up as Background Asyncio Task

**Date:** Phase 6

**Problem:** Follow-up reminders must be sent to leads who did not respond. No external job scheduler is available.

**Alternatives:**
- External scheduler (Redis Queue, Celery, APScheduler)
- Polling loop inside the application
- In-memory timers

**Chosen Solution:** `FollowUpEngine` runs an asyncio background task that polls the database every N seconds (`poll_interval_seconds`), selects due tasks, and sends them.

**Reason:** No external dependencies. Tasks survive restarts (stored in SQLite). Polling interval is configurable via `followup.json`. Optimistic locking (`UPDATE … WHERE status='pending'`) prevents double execution.

**Trade-offs:** Polling is less precise than event-driven scheduling. At 1000+ active leads, the sequential loop needs concurrency (out of scope for MVP).

**Status:** ACTIVE

---

## Decision 006 — Conversation History as Structured Summaries

**Date:** Phase 2

**Problem:** Storing raw transcripts consumes space, risks leaking PII, and makes context building expensive.

**Alternatives:**
- Full transcript storage
- Structured summaries only

**Chosen Solution:** Store a 500-character summary of the conversation. Each turn appends a short description like `"User asked about faq"`.

**Reason:** The LLM only needs context, not verbatim history. Summaries are cheaper, safer, and sufficient for qualification.

**Trade-offs:** Some nuance may be lost. The summary format is hardcoded in `_apply_extracted_fields`.

**Status:** ACTIVE