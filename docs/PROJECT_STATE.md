# Project State

## What this project is
DentalFlow AI is a reusable AI receptionist and lead automation framework.  
It is designed as a portfolio-grade commercial MVP that can later be adapted to other businesses by changing client configuration files.

## Phase Status

Current Phase: **Phase 10.2 — Backup БД (scheduled backup, rotation, restore, integrity)**

Status: **COMPLETE** (implementation finished; awaiting APPROVE)

Next Action: Phase 10.3 — Analytics dashboard (see docs/ROADMAP.md).

Current Reviewer: **DeepSeek V4 Pro (Architect)**

Current Developer: **DeepSeek V4 Flash (Developer)**

Current Git Tag: **v0.10.1**

Last Updated: 2026-08-03

## Current status
Completed:
- Phase 0: project scaffold — MERGED
- Phase 1: client config + storage — MERGED
- Phase 2: AI layer with structured output — MERGED
- Phase 3: business rules, validation, safety, state machine — MERGED
- Phase 4: Telegram channel integration — MERGED
- Phase 5: CRM and notifications — MERGED
- Phase 6: follow-up engine — MERGED
- Phase 7: polish and portfolio readiness — MERGED
- Phase 8: multi-channel support — MERGED
- Phase 9A: Docker production image — MERGED
- Phase 9B.1: Extract entry points — MERGED
- Phase 10.1: Monitoring — watchdog, Telegram alerts, /metrics — MERGED (v0.10.1)
- Phase 10.2: Backup БД — scheduled backup, rotation, restore, integrity — DONE (pending review)

ADR 002 (JSON-driven core scope) — ACCEPTED. 225 tests passing, ruff clean.

Next:
- Phase 10.3: Analytics dashboard (see docs/ROADMAP.md)

## Core architecture decisions
- Telegram is only a transport channel.
- Business-specific content lives in client JSON files.
- LLM returns structured output only.
- Python validates all critical actions.
- CRM access goes through provider interfaces.
- Mock CRM is used for demo and tests.
- Conversation history is stored as structured summaries, not raw transcripts.

Full decision records: see `docs/ARCHITECTURE_DECISIONS.md`.

## Files to read first
1. AGENTS.md
2. docs/ENGINEERING_PLAYBOOK.md
3. docs/DEFINITION_OF_DONE.md
4. docs/PROJECT_STATE.md
5. docs/PROJECT_CONVENTIONS.md
6. docs/ARCHITECTURE_DECISIONS.md
7. docs/BACKLOG.md
8. clients/demo_dental/
9. src/

## Important constraints
- Do not reintroduce hardcoded business text into Python.
- Do not move business logic back into Telegram handlers.
- Do not let the LLM control CRM writes directly.
- Keep changes small and phase-based.
- Stop after each phase and wait for approval.
- After APPROVE, new ideas go to `docs/BACKLOG.md`, not back into the current phase.

## Known Limitations

См. [BACKLOG.md](BACKLOG.md) — задокументированы:
- `_response_store` (утечка памяти, не переживает рестарт)
- Дублирование кода между каналами
- Прочие архитектурные замечания

Не блокируют релиз v0.9.10, запланированы на Phase 11.

## Known Limitations

См. [BACKLOG.md](BACKLOG.md) — задокументированы:
- `_response_store` (утечка памяти, не переживает рестарт)
- Дублирование кода между каналами
- Прочие архитектурные замечания

Не блокируют релиз v0.9.10, запланированы на Phase 11.

## Known Limitations

См. [BACKLOG.md](BACKLOG.md) — задокументированы:
- `_response_store` (утечка памяти, не переживает рестарт)
- Дублирование кода между каналами (планируется вынести в lead_lookup.py)
- Прочие архитектурные замечания (SingletonConnection, data classes, temperature)

Не блокируют релиз v0.9.10, запланированы на Phase 11.
