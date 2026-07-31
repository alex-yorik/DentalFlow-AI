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

## QA Rules (MANDATORY)

After APPROVE:
- Stop review cycle immediately.
- Do not search for additional improvements.
- Do not start another architecture review.
- Do not start another QA review.
- Recommend merge, commit, push, and git tag.

Avoid endless review loops.

## Mandatory Context Policy

Before starting any task, the agent MUST:

1. **Classify** the task type using `docs/process/task_classifier.md`.
2. **Determine** the allowed file list using `docs/process/file_scope.md`.
3. **Read** only files on the allowed list.
4. **Stop reading** as soon as sufficient information is available.
5. If a file outside the allowed list is needed, **stop** and explicitly name it.

## Forbidden Behaviour

The agent MUST NOT:

- Scan `docs/` or any directory recursively.
- Open README.md automatically.
- Inspect unrelated tests.
- Inspect unrelated source code.
- Inspect unrelated configuration files.
- Open additional documentation "just in case".

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
