# ADR 002: Scope of JSON-Driven Core

**Date:** 2026-08-03
**Status:** Accepted
**Context:** Phase 11.1 completed (scoring rules extensibility)

## Decision

We will NOT pursue full JSON-driven core (dynamic Lead fields, arbitrary business forms) at this time.

**Rationale:**
1. No second real client with different requirements yet
2. Would break Pydantic type safety
3. Requires redesigning 5+ core modules (Lead, LLM contracts, state machine, DB schema)
4. Violates "Rule of Three" — don't abstract before seeing the problem twice

**Scope fixed as:** Conversational lead qualification for **appointment-based service businesses** (dental, auto repair, salons, consultations).

## Consequences

**Positive:**
- Maintain type safety and testability
- Avoid over-engineering
- Faster delivery for current target segment

**Negative:**
- New clients outside this pattern require forking/adapting core modules
- Not a "universal platform" yet

## Triggers for Reconsideration

When we get a second real client with a lead form that doesn't fit the current model (name/phone/email/service/urgency), we will revisit this decision with concrete requirements.

## What We Did Instead

- Phase 11.1: Scoring rules extensibility via JSON (done)
- New clients in same segment → new `clients/*` folder, core unchanged
- Full JSON-driven core → moved to BACKLOG.md
