# DentalFlow AI Project Rules

## Goal
Build a production-oriented portfolio MVP for an AI receptionist and lead automation system.

## Core Principles
- Preserve working code unless a change is clearly needed.
- Keep changes small and isolated.
- Separate channels, AI logic, business rules, storage, and integrations.
- AI proposes, Python validates and decides.
- Use configuration files for client-specific behavior whenever possible.
- Do not invent prices, availability, medical advice, or guarantees.
- Do not let the LLM write directly to protected systems.
- **Planning MUST treat token cost as an architectural constraint** — every file read, every word generated, every table included has a measurable cost.

## Architecture Expectations
- Telegram is only the first channel.
- The core must later support web and WhatsApp without rewrites.
- Lead handling must be a state machine.
- CRM access must go through provider interfaces.
- Follow-up must be a separate subsystem.

## Working Style
- First analyze, then plan, then implement.
- If requirements are unclear, ask instead of guessing.
- Keep documentation and code aligned.
- **Do not repeat existing DoD, Workflow, Architecture, or Process definitions. Use short references instead.**

## QA Rules (MANDATORY)

After APPROVE:
- Stop review cycle immediately.
- Do not search for additional improvements.
- Do not start another architecture review.
- Do not start another QA review.
- Recommend merge, commit, push, and git tag.

Avoid endless review loops.

## Workflow
Follow docs/process/WORKFLOW.md

## Handoff
Generate minimal prompt for next role (see WORKFLOW.md)

## Mandatory Rules for Flash

Flash MUST:
- Work only within Allowed Files
- Stop after completing the task
- NOT search for additional problems
- NOT perform refactoring unless requested
- NOT read additional files

## Forbidden Behaviour

The agent MUST NOT:
- Scan docs/ or any directory recursively
- Open README.md automatically
- Inspect unrelated tests or source code
- Open additional documentation "just in case"
- Create new documentation without explicit request

## Context Policy
Before starting any task:
1. Classify task type (use WORKFLOW.md table)
2. Determine Allowed Files
3. Read ONLY Allowed Files
4. Stop when sufficient information obtained
5. If need file outside Allowed Files → stop and ask

## Restricted Mode

For any task, the architect (Pro) may pass an explicit `Allowed Files` list.
The agent (Flash) MUST work exclusively within this list.

If a needed file is missing from the list, the agent must stop and request permission.

### Example — Restricted Mode

```
Allowed Files:
  src/followup/__init__.py
  tests/unit/test_followup.py
```

The agent is NOT permitted to open:
- README.md
- AGENTS.md
- docs/PROJECT_STATE.md
- Any other test file
- Any other source module