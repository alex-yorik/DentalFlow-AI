# Project State

## What this project is
DentalFlow AI is a reusable AI receptionist and lead automation framework.  
It is designed as a portfolio-grade commercial MVP that can later be adapted to other businesses by changing client configuration files.

## Current status
Completed:
- Phase 0: project scaffold
- Phase 1: client config + storage
- Phase 2: AI layer with structured output
- Phase 3: business rules, validation, safety, state machine
- Phase 4: Telegram channel integration
- Phase 5: CRM and notifications

Next:
- Phase 6: follow-up engine
- Phase 7: polish and portfolio readiness

## Core architecture decisions
- Telegram is only a transport channel.
- Business-specific content lives in client JSON files.
- LLM returns structured output only.
- Python validates all critical actions.
- CRM access goes through provider interfaces.
- Mock CRM is used for demo and tests.
- Conversation history is stored as structured summaries, not raw transcripts.

## Files to read first
1. AGENTS.md
2. docs/IMPLEMENTATION_PLAN.md
3. docs/PROJECT_STATE.md
4. docs/PROJECT_CONVENTIONS.md
5. clients/demo_dental/
6. src/

## Important constraints
- Do not reintroduce hardcoded business text into Python.
- Do not move business logic back into Telegram handlers.
- Do not let the LLM control CRM writes directly.
- Keep changes small and phase-based.
- Stop after each phase and wait for approval.
