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
| v0.7.0 | 2026-08-01 | Phase 7: Polish and portfolio readiness ✅ |
| v0.8.0 | 2026-08-01 | Phase 8: Multi-channel support ✅ |
| v0.9.0 | TBD | Phase 9: Production Deployment 🔄 |

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

### Phase 7: Polish and Portfolio Readiness ✅
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
- Git tag: v0.7.19

### Phase 8: Multi-Channel Support ✅
**Goal:** Make core channel-agnostic, add Web and WhatsApp channels.

**Subphases:**
- 8A: Channel abstraction + extract core ✅ (v0.8.0)
  - Created IncomingMessage/OutgoingAdapter protocols
  - Extracted process_message() to core/message_processor.py
  - Added channel_type column to leads
- 8B: Web channel (FastAPI + HTML chat) ✅ (v0.8.1)
- 8C: WhatsApp stub (architecture + adapter stub) ✅ (v0.8.2)

**Result:** 3 channels (Telegram, Web, WhatsApp) work through unified process_message(). All 152 tests pass.

---

## Current Phase

### Phase 9: Production Deployment 🔄
**Goal:** Make project production-ready with Docker, CI/CD, and monitoring.

**Status:** In progress (9B.2 — NEXT)

**Subphases:**

#### 9A: Docker Production Image ✅ (v0.9.0)
**Status:** DONE
**What was done:**
- Multi-stage Dockerfile (builder + runtime)
- Non-root user (appuser)
- HEALTHCHECK instruction
- .dockerignore
- Docker Compose for local dev
- Memory/CPU limits

#### 9B: Service Separation 🔄
**Goal:** Split monolith into independently deployable services with proper healthcheck parameterization.

**Subphases:**
- **9B.1: Extract entry points ✅ (v0.9.1)**
  - Extracted bootstrap() with shared init (config, LLMClient)
  - Created independent entry points: telegram (bot + followup), web (uvicorn), followup (engine only)
  - Refactored main.py to delegate to entrypoints
  - All 152 tests pass
- **9B.2: Docker healthcheck parameterization — NEXT**
  - Replace hardcoded healthcheck with env-var-driven parameters
  - Extract healthcheck script to docker/healthcheck.py
  - Parameterize interval, timeout, retries
- **9B.3: Multi-service Docker Compose — TBD**
  - Split docker-compose into separate services per entry point
  - Shared data volume for SQLite
- **9B.4: Nginx reverse proxy — TBD**
  - Nginx as entry point for web traffic
  - Let's Encrypt for HTTPS
- **9B.5: Integration test — TBD**
  - Test multi-service startup and healthcheck chain

#### 9C: Structured Logging — TBD
- JSON format logging
- Log levels per environment
- Request ID tracing

#### 9D: CI/CD Pipeline — TBD
- GitHub Actions workflow
- Automated testing on PR
- Automated deployment on merge
- Tag-based versioning

#### 9E: Database Migrations — TBD
- Alembic integration
- Migration scripts for schema changes
- Rollback capability

#### 9F: Environment Configuration — TBD
- Multi-environment configs (dev/staging/prod)
- Secret management (env files, vault)
- Feature flags

#### 9G: Fix Phase 8 Debts — TBD
- FollowUpEngine still uses telegram.Bot directly (should use channel-agnostic adapter)
- notifications.py still uses telegram.Bot directly (should use channel-agnostic adapter)

---

## Future Phases (Planned)

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

---

## Backlog (Low Priority)
See docs/BACKLOG.md for detailed list.

Key items:
- Convert dataclasses to Pydantic (4.1)
- Clarify apply_transition() return value (4.2)
- Fix _fallback() intent semantics (4.3)
- Move temperature=0.1 to AppConfig (4.4)

---

## Architecture Decisions
See docs/ARCHITECTURE_DECISIONS.md

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

### v0.7.x — Polish and Portfolio Readiness ✅
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
- **v0.7.19: Phase 7 complete** ✅

### v0.8.x — Multi-Channel Support ✅
- v0.8.0: Channel abstraction ✅
- v0.8.1: Web channel ✅
- v0.8.2: WhatsApp stub ✅
- **v0.8.3: Phase 8 complete** ✅

### v0.9.x — Production Deployment 🔄
- v0.9.0: Docker production image ✅
- v0.9.1: Entry points extraction ✅
- v0.9.2: Docker healthcheck parameterization — NEXT
- v0.9.3: Multi-service Compose — TBD
- v0.9.4: Nginx reverse proxy — TBD
- v0.9.5: Integration test — TBD
- **v0.9.6: Phase 9 complete** — TBD

### v1.0.0 — First Stable Release
- All critical features complete
- Production deployment tested
- Documentation complete
- Client onboarding working

---

**Last Updated:** 2026-08-02  
**Current Version:** v0.9.1 (Phase 9B.1 complete)  
**Next Milestone:** v0.9.2 (Phase 9B.2: Docker healthcheck parameterization)