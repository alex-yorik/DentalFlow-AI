
# DentalFlow-AI Roadmap

## Project Overview
**DentalFlow AI** — reusable AI receptionist and lead automation framework for dental clinics.  
Designed as **portfolio-grade commercial MVP**, adaptable to other businesses via client JSON config files.

**Core Architecture Principles:**
- Telegram is only a transport channel (core is channel-agnostic)
- Business-specific content lives in client JSON files
- LLM returns structured output only (Pydantic-validated)
- Python validates all critical actions (LLM is untrusted)
- CRM access goes through provider interfaces
- Mock CRM is used for demo and tests
- Conversation history is stored as structured summaries, not raw transcripts

---

## Version History

| Version | Date | Milestone |
|---------|------|-----------|
| v0.0.1 | 2026-07-31 | Phase 0: Project scaffold |
| v0.1.0 | 2026-07-31 | Phase 1: Client config + storage |
| v0.2.0 | 2026-07-31 | Phase 2: AI layer with structured output |
| v0.3.0 | 2026-07-31 | Phase 3: Business rules, validation, safety, state machine |
| v0.4.0 | 2026-07-31 | Phase 4: Telegram channel integration |
| v0.5.0 | 2026-07-31 | Phase 5: CRM and notifications |
| v0.6.0 | 2026-07-31 | Phase 6: Follow-up engine |
| v0.7.0 | 2026-08-01 | Phase 7: Polish and portfolio readiness (IN PROGRESS) |
| v0.8.0 | TBD | Phase 8: Multi-channel support (PLANNED) |

---

## Completed Phases

### Phase 0-6: MVP Foundation ✅
- Project scaffold
- Client config + storage
- AI layer with structured output
- Business rules, validation, safety, state machine
- Telegram channel integration
- CRM and notifications
- Follow-up engine

### Phase 7: Polish and Portfolio Readiness 🔄
- 7B: Documentation accuracy ✅
- 7C: Quality documentation (testing.md, security.md) ✅
- 7D.1: Input Security (refusal counter, sanitization, rate limiting) ✅
- 7D.2.1: DB error handling (StorageError, repository wrappers) ✅
- 7D.2.2: Handler Error Recovery (try/except in handle_message) ✅
- 7D.2.3: Startup + Graceful Shutdown ✅
- 7D.2.4: is_fallback flag + unified notifications ✅
- 7D.2.5: Consolidate _write_to_crm + score_rules validation ✅
- 7D.2.6: Word boundaries in check_safety() ✅
- 7D.2.7: Lead field validation (phone/email) ✅
- 7D.2.8: SQLite connection pooling ✅
- Testing Debt: is_fallback + notifications unit tests ✅

## Current Phase

### Phase 8: Multi-Channel Support 🔄
**Goal:** Make core channel-agnostic, add Web and WhatsApp channels.

**Status:** In progress

**Subphases:**
- 8A: Channel abstraction + extract core (DONE ✅)
  - Created IncomingMessage/OutgoingAdapter protocols
  - Extracted process_message() to core/message_processor.py
  - Added channel_type column to leads
  - 152 tests pass
- 8B: Web-channel (FastAPI + HTML chat) — NEXT
- 8C: WhatsApp-channel (architecture + stub) — TBD

## Future Phases (Planned)

### Phase 9: Production Deployment
- Docker production setup (multi-stage builds, health checks)
- Environment-based configuration (dev/staging/prod)
- Monitoring and alerting (structured logging, metrics)
- CI/CD pipeline (GitHub Actions)
- Database migrations system

### Phase 10: Advanced Features
- Analytics dashboard (conversation metrics, conversion rates)
- A/B testing for AI responses
- Custom AI training per client
- Advanced follow-up scenarios

### Phase 11: Client Onboarding
- Self-service client setup wizard
- Config validation UI
- Template system for common clinic types
- Automated testing per client config

## Backlog (Low Priority)
See docs/BACKLOG.md for detailed list.

Key items:
- Convert dataclasses to Pydantic (4.1)
- Clarify apply_transition() return value (4.2)
- Fix _fallback() intent semantics (4.3)
- Move temperature=0.1 to AppConfig (4.4)

## Architecture Decisions
See docs/ARCHITECTURE_DECISIONS.md

## How to Use This Document
When starting a new session:
1. Read this file to understand project status
2. Check "Current Phase" for what to work on
3. Check "Future Phases" for long-term direction
4. Check "Backlog" for low-priority items

# DentalFlow-AI Roadmap

## Project Overview
**DentalFlow AI** — reusable AI receptionist and lead automation framework for dental clinics.  
Designed as **portfolio-grade commercial MVP**, adaptable to other businesses via client JSON config files.

**Core Architecture Principles:**
- Telegram is only a transport channel (core is channel-agnostic)
- Business-specific content lives in client JSON files
- LLM returns structured output only (Pydantic-validated)
- Python validates all critical actions (LLM is untrusted)
- CRM access goes through provider interfaces
- Mock CRM is used for demo and tests
- Conversation history is stored as structured summaries, not raw transcripts

---

## Version History

| Version | Date | Milestone |
|---------|------|-----------|
| v0.0.1 | 2026-07-31 | Phase 0: Project scaffold |
| v0.1.0 | 2026-07-31 | Phase 1: Client config + storage |
| v0.2.0 | 2026-07-31 | Phase 2: AI layer with structured output |
| v0.3.0 | 2026-07-31 | Phase 3: Business rules, validation, safety, state machine |
| v0.4.0 | 2026-07-31 | Phase 4: Telegram channel integration |
| v0.5.0 | 2026-07-31 | Phase 5: CRM and notifications |
| v0.6.0 | 2026-07-31 | Phase 6: Follow-up engine |
| v0.7.0 | 2026-08-01 | Phase 7: Polish and portfolio readiness (IN PROGRESS) |
| v0.8.0 | TBD | Phase 8: Multi-channel support (PLANNED) |

---

## Completed Phases

### Phase 0: Project Scaffold ✅
- Basic project structure
- GitHub repo setup
- Initial dependencies

### Phase 1: Client Config + Storage ✅
- Client JSON configuration system
- SQLite database with aiosqlite
- Basic lead storage

### Phase 2: AI Layer with Structured Output ✅
- OpenAI API integration
- Pydantic-structured outputs
- Intent classification
- Field extraction

### Phase 3: Business Rules, Validation, Safety, State Machine ✅
- State machine for lead qualification
- Safety checks (blocked phrases, unsafe intents)
- Output validation (confidence thresholds)
- Business rules enforcement

### Phase 4: Telegram Channel Integration ✅
- python-telegram-bot integration
- Message handlers
- Command handlers (/start, etc.)

### Phase 5: CRM and Notifications ✅
- CRM provider interface
- Mock CRM for demo
- Staff notifications
- Lead creation in CRM

### Phase 6: Follow-up Engine ✅
- Scheduled follow-up tasks
- Task cancellation
- Re-engagement after inactivity

### Phase 7: Polish and Portfolio Readiness 🔄

#### 7A: (skipped)

#### 7B: Documentation Accuracy ✅
- Fixed file reference errors in docs/architecture.md
- Fixed file reference errors in docs/dentalflow.md
- All paths now match actual project structure
- Git tag: v0.7.1-docs-accuracy

#### 7C: Quality Documentation ✅
- Created docs/testing.md (pytest framework, test categories, fixtures)
- Created docs/security.md (threat model, safety layers, known gaps)
- 114 + 135 lines of technical documentation
- Git tag: v0.7.3-quality-docs

#### 7D: Error Handling & Security Hardening ✅

**7D.1: Input Security ✅**
- Refusal counter (Lead.refusal_count, check_safety)
- Input sanitization (_sanitize_input, 2000 char limit)
- Rate limiting (10 msg / 60s per chat_id, in-memory deque)
- All 142 tests passed
- Git tag: v0.7.4-input-security

**7D.2.1: DB Error Handling ✅**
- StorageError custom exception
- Wrapped 5 repository functions in try/except
- Wrapped 6 followup functions in try/except
- Contextual logging (chat_id, lead_id, operation)
- Graceful degradation (None instead of crash)
- Git tag: v0.7.5-error-handling

**7D.2.2: Handler Error Recovery ✅**
- handle_message() wrapped in top-level try/except
- Nested try/except for reply_text failures
- User receives error_generic on unexpected errors
- 145 tests pass
- Git tag: v0.7.10-handler-error-recovery

**7D.2.3: Startup + Graceful Shutdown ✅**
- init_db(), create_bot(), followup_engine.start() wrapped in try/except
- try/finally guarantees cleanup on any failure
- Partial initialization handled (bot works even if followup fails)
- Git tag: v0.7.11-phase-7d2-complete

**7D.2.4: is_fallback Flag + Unified Notifications ✅**
- Added is_fallback: bool flag to AIOutput (replaces magic confidence==0.0)
- Unify notifications: move followup notification to integrations/notifications.py
- Updated docs/security.md Known Gaps table
- 145 tests pass
- Git tag: v0.7.9-fallback-notifications

**7D.2.5: Consolidate _write_to_crm + Score Rules Validation ✅**
- Consolidated duplicate _write_to_crm() calls (audit 2.3)
- Added Pydantic validation for score_rules keys (audit 2.4)
- Prevents typos like 'has_pnone' instead of 'has_phone'
- 148 tests pass
- Git tag: v0.7.14-score-rules-validation

**7D.2.6: Word Boundaries in check_safety() ✅**
- Replaced substring matching with \b word boundaries + re.IGNORECASE
- Prevents false positives: 'cure' no longer blocks 'curettage' (dental term)
- Prevents false positives: 'free' no longer blocks 'freelance'
- Added 4 new tests for word boundary cases
- 152 tests pass (was 148, +4 new)
- Git tag: v0.7.15-word-boundary-safety

**7D.2.7: Lead Field Validation ✅**
- Added PHONE_PATTERN and EMAIL_PATTERN regex validation
- Pydantic validators log warnings for invalid formats
- Validation is soft (logs but accepts) — doesn't reject LLM-extracted fields
- 152/152 tests pass
- Git tag: v0.7.17-lead-field-validation

**7D.2.8: SQLite Connection Pooling ✅**
- Implemented _SingletonConnection proxy wrapper around aiosqlite.Connection
- get_connection() returns singleton (one connection for production)
- conn.close() is no-op (preserves singleton)
- close_connection() performs actual shutdown
- Tests use conftest.py to get real connections (isolation preserved)
- 152/152 tests pass
- Git tag: v0.7.18-sqlite-pooling

**Testing Debt (High Priority from Audit) ✅**
- Added explicit is_fallback assertions to fallback tests
- Created test_notifications.py with 3 tests for notify_staff_followup_complete
- 148/148 tests pass (was 145, +3 new)
- Git tag: v0.7.12-testing-debt-high-priority

---

## Current Phase

### Phase 8: Multi-Channel Support 🔄
**Goal:** Make core channel-agnostic, add Web and WhatsApp channels.

**Status:** In progress (8A complete, 8B next)

**Subphases:**

#### 8A: Channel Abstraction + Extract Core ✅
**Status:** DONE (APPROVED)

**What was done:**
- Created `src/channels/base.py` with protocols:
  - IncomingMessage dataclass (channel_user_id, text, channel_type)
  - OutgoingAdapter protocol with send_message(channel_user_id, text)
- Created `src/core/message_processor.py` — channel-independent process_message()
  - Extracted: sanitize_input(), build_context(), apply_extracted_fields(), try_advance_lead(), _write_to_crm()
  - Accepts: IncomingMessage, OutgoingAdapter, lead, config, llm_client, optionally followup_engine and bot_for_notifications
- Refactored `src/channels/telegram/handlers.py` to thin adapter (270→90 lines)
  - TelegramOutgoingAdapter wraps update.message.reply_text
  - handle_message() is now thin adapter: extract text, rate limit, lookup lead, instantiate adapter, delegate to process_message()
- Added `channel_type: str = "telegram"` to Lead model (without deleting telegram_chat_id)
- Added migration: ALTER TABLE leads ADD COLUMN channel_type TEXT NOT NULL DEFAULT 'telegram'
- Updated repository.py to save/read channel_type
- All 152 tests pass

**Files changed:**
- src/channels/base.py (new)
- src/core/message_processor.py (new)
- src/channels/telegram/handlers.py (refactored)
- src/leads/models.py
- src/storage/migrations.py
- src/leads/repository.py
- src/storage/database.py

**What was NOT changed:**
- telegram_chat_id — not renamed
- FollowUpEngine — still uses telegram.Bot (will be in 8B)
- notifications.py — no changes yet
- All tests — no modifications

**Git tag:** v0.8.0-multi-channel-abstract

---

#### 8B: Web-Channel (FastAPI + HTML Chat) — NEXT
**Goal:** Add web interface — REST API for chat + minimal HTML widget.

**Files to create/modify:**
- src/channels/web/__init__.py (new) — FastAPI app
- src/channels/web/adapter.py (new) — WebOutgoingAdapter, binds to process_message
- src/channels/web/templates/chat.html (new) — minimal HTML widget
- src/main.py — run FastAPI alongside Telegram
- src/config/loader.py — config for web channel (port, CORS)

**Tasks:**
1. FastAPI endpoint — POST /api/chat accepts {channel_id, text}, calls process_message(), returns reply_text
2. WebOutgoingAdapter — saves responses in in-memory queue (for polling from HTML widget) or returns via Server-Sent Events
3. HTML-chat widget — minimal interface: input field, message history, polling for responses

**Definition of Done:**
- curl -X POST .../api/chat returns meaningful response
- HTML widget displays dialog
- Telegram channel continues working without regression
- All existing tests pass (152+)

---

#### 8C: WhatsApp-Channel (Architecture + Stub)
**Goal:** Design WhatsApp integration, implement adapter-stub (without real credentials).

**Files to create:**
- src/channels/whatsapp/__init__.py (new)
- src/channels/whatsapp/adapter.py (new) — WhatsAppAdapter (stub)
- docs/architecture/whatsapp-integration.md (new) — webhook flow architecture

**Tasks:**
1. WhatsApp architecture — describe webhook flow: Meta Business API → webhook verification → incoming message → process_message() → send via WhatsApp Cloud API
2. WhatsAppAdapter stub — WhatsAppOutgoingAdapter with stub instead of real HTTP calls (logs messages). Ready to replace with real HTTP client when credentials appear.

**Definition of Done:**
- WhatsApp adapter compiles, stub logs messages
- Documentation describes full webhook flow
- No real credentials required

---

### Overall Definition of Done for Phase 8:
- 3 channels (Telegram, Web, WhatsApp) work through unified process_message()
- All existing tests pass
- Telegram behavior unchanged
- New channel (web) demonstrates full FAQ + lead capture cycle

---

## Future Phases (Planned)

### Phase 9: Production Deployment
**Goal:** Make project production-ready with Docker, CI/CD, and monitoring.

**Subphases:**
- 9A: Docker production setup
  - Multi-stage builds
  - Health checks
  - Environment variables management
  - Docker Compose for local dev
  
- 9B: Environment-based configuration
  - dev/staging/prod configs
  - Secret management (.env files, vault)
  - Feature flags
  
- 9C: Monitoring and alerting
  - Structured logging (JSON format)
  - Metrics (Prometheus-compatible)
  - Error tracking (Sentry integration)
  - Performance monitoring
  
- 9D: CI/CD pipeline
  - GitHub Actions workflow
  - Automated testing on PR
  - Automated deployment on merge
  - Tag-based versioning
  
- 9E: Database migrations system
  - Alembic integration
  - Migration scripts for schema changes
  - Rollback capability

**Success Criteria:**
- One-command deployment to production
- Zero-downtime deployments
- Automated rollback on failure
- Full observability (logs, metrics, traces)

---

### Phase 10: Advanced Features
**Goal:** Add advanced features for commercial viability.

**Subphases:**
- 10A: Analytics dashboard
  - Conversation metrics (total, by channel, by intent)
  - Conversion rates (lead → customer)
  - Response time metrics
  - User engagement metrics
  
- 10B: A/B testing for AI responses
  - Multiple response templates
  - Random assignment
  - Performance tracking
  - Automatic winner selection
  
- 10C: Custom AI training per client
  - Client-specific fine-tuning
  - Custom knowledge base ingestion
  - Domain-specific intent classification
  
- 10D: Advanced follow-up scenarios
  - Multi-step reminder sequences
  - Conditional branching based on user response
  - Time-based escalation rules

**Success Criteria:**
- Dashboard accessible via web UI
- A/B tests can be configured via admin panel
- Client-specific models can be trained without code changes
- Follow-up sequences are configurable per client

---

### Phase 11: Client Onboarding System
**Goal:** Enable self-service client setup and configuration.

**Subphases:**
- 11A: Self-service client setup wizard
  - Web UI for new client registration
  - Step-by-step configuration
  - CRM connection setup
  - Testing sandbox
  
- 11B: Config validation UI
  - Real-time validation feedback
  - Visual rule editor
  - Test mode for config changes
  
- 11C: Template system for common clinic types
  - Pre-configured templates (general dentistry, orthodontics, etc.)
  - Customizable templates
  - Template marketplace
  
- 11D: Automated testing per client config
  - Automated test generation from config
  - Regression testing on config changes
  - Performance benchmarking

**Success Criteria:**
- New client can be onboarded in <30 minutes
- No code changes required for new clients
- Config validation prevents deployment of broken configs
- Templates cover 80% of common use cases

---

## Backlog (Low Priority)

See `docs/BACKLOG.md` for detailed list.

### Key Items:

#### Code Consistency (4.x)
- **4.1:** Convert dataclasses to Pydantic models
  - TransitionResult (leads/state_machine.py)
  - SafetyVerdict (rules/safety.py)
  - ValidationResult (rules/validator.py)
  - QualificationResult (rules/qualification.py)
  
- **4.2:** Clarify apply_transition() return value
  - Currently mutates AND returns lead (confusing)
  - Either return None (pure mutation) or return new lead (immutable)
  
- **4.3:** Fix LLMClient._fallback() intent semantics
  - Currently sets intent=Intent.OFF_TOPIC (misleading)
  - Should be intent=Intent.ERROR or separate field
  
- **4.4:** Move temperature=0.1 to AppConfig
  - Currently hardcoded in llm/client.py
  - Should be configurable via env

#### Performance & Reliability (Already Done ✅)
- ~~3.1: SQLite connection pooling~~ ✅ (v0.7.18)
- ~~3.2: Cleanup stale chat_ids in _rate_limit dict~~ ✅ (v0.7.16)
- ~~3.3: Word boundaries in check_safety()~~ ✅ (v0.7.15)
- ~~3.4: Lead field validation~~ ✅ (v0.7.17)

---

## Architecture Decisions

See `docs/ARCHITECTURE_DECISIONS.md` for detailed records.

Key decisions:
- Telegram is only a transport channel
- LLM is untrusted — Python validates all critical actions
- Business logic lives in client JSON files, not in code
- CRM access goes through provider interfaces
- Conversation history stored as structured summaries

---

## How to Use This Document

### When Starting a New Session:

1. **Read this file FIRST** (before any other files)
2. **Check "Current Phase"** for what to work on next
3. **Check "Future Phases"** for long-term direction
4. **Check "Backlog"** for low-priority items
5. **Do NOT ask "what should we do next?"** — this document has the answer

### When Planning a New Subphase:

1. Identify the subphase from the plan
2. Create detailed task breakdown
3. Specify allowed files (max 5 per task)
4. Define Definition of Done
5. Generate PROMPT FOR FLASH

### When Completing a Subphase:

1. Update version number in Version History
2. Add git tag to Completed Phases section
3. Mark subphase as DONE ✅
4. Update PROJECT_STATE.md
5. Move to next subphase

---

## Metrics & Goals

### Code Quality Metrics
- Test coverage: 152 tests (100% of critical paths)
- Type safety: Pydantic models for all configs and outputs
- Error handling: All external calls wrapped in try/except
- Documentation: All public APIs documented

### Performance Goals
- Response time: <2s for AI responses
- Database: Connection pooling implemented
- Memory: No unbounded growth (rate_limit dict cleanup)
- Concurrency: WAL mode for SQLite

### Security Goals
- Input validation: All user input sanitized
- Output validation: All LLM outputs validated
- Rate limiting: 10 msg/60s per user
- Safety checks: Blocked phrases, unsafe intents
- Secret management: All tokens in .env, not in code

---

## Release Schedule

### v0.7.x — Polish and Portfolio Readiness (IN PROGRESS)
- v0.7.1: Documentation accuracy ✅
- v0.7.3: Quality documentation ✅
- v0.7.4: Input security ✅
- v0.7.5: DB error handling ✅
- v0.7.10: Handler error recovery ✅
- v0.7.11: Startup/shutdown ✅
- v0.7.12: Testing debt ✅
- v0.7.14: Score rules validation ✅
- v0.7.15: Word boundary safety ✅
- v0.7.17: Lead field validation ✅
- v0.7.18: SQLite pooling ✅
- **v0.7.19: Phase 7 complete** — READY FOR RELEASE

### v0.8.x — Multi-Channel Support (PLANNED)
- v0.8.0: Channel abstraction ✅
- v0.8.1: Web channel
- v0.8.2: WhatsApp stub
- **v0.8.3: Phase 8 complete**

### v0.9.x — Production Deployment (FUTURE)
- v0.9.0: Docker setup
- v0.9.1: CI/CD pipeline
- v0.9.2: Monitoring
- **v0.9.3: Phase 9 complete** — PRODUCTION READY

### v1.0.0 — First Stable Release
- All critical features complete
- Production deployment tested
- Documentation complete
- Client onboarding working

---

**Last Updated:** 2026-08-01  
**Current Version:** v0.8.0 (Phase 8A complete)  
**Next Milestone:** v0.8.1 (Phase 8B: Web channel)
