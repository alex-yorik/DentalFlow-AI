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

## Mandatory Rules for Flash

Flash MUST:

1. **Work only within Allowed Files** — never read or modify files outside the list.
2. **Stop after completing the task** — do not start the next subphase.
3. **Not search for additional problems** — do not look for bugs, tech debt, or improvements not in scope.
4. **Not perform refactoring** — unless explicitly requested by Pro.
5. **Not read additional files** — if a file is needed outside Allowed Files, stop and ask Pro.

## Mandatory Context Policy

Before starting any task, the agent MUST:

1. **Classify** the task type using `docs/process/task_classifier.md`.
2. **Determine** the allowed file list using `docs/process/file_scope.md`.
3. **Read** only files on the allowed list.
4. **Stop reading** as soon as sufficient information is available.
5. If a file outside the allowed list is needed, **stop** and explicitly name it.

**This policy applies to ALL roles — Pro (Planner) and Flash (Developer).**
**Planner reads only Allowed Files of the current subphase. Reading extra files "just in case" is forbidden.**

## Forbidden Behaviour

The agent MUST NOT:

- Scan `docs/` or any directory recursively.
- Open README.md automatically.
- Inspect unrelated tests.
- Inspect unrelated source code.
- Inspect unrelated configuration files.
- Open additional documentation "just in case".
- **Create new documentation files without explicit request.**
- **Create new process sections without necessity. Integrate changes into existing sections.**

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

## Workflow Handoff Protocol (MANDATORY)

Каждая модель обязана завершать работу **token-minimal handoff-блоком** для следующей модели.

### Формат блоков

```
====================
PROMPT FOR FLASH
====================
<цель, Allowed Files, Forbidden Files, DoD, тесты, Stop Condition>

====================
PROMPT FOR PRO QA
====================
<список изменённых файлов, что проверять, ожидаемый результат>

====================
PROMPT FOR PRO (NEXT PHASE)
====================
<контекст завершённой подфазы и запрос на планирование следующей>
```

### Обязательные правила (MANDATORY)

1. **Pro (Planning)** — генерирует `PROMPT FOR FLASH` с полным заданием для Flash.
2. **Flash (Build)** — генерирует `PROMPT FOR PRO QA` с перечнем изменений для проверки.
3. **Pro (QA, REQUEST_CHANGES)** — генерирует `PROMPT FOR FLASH` только с исправлениями. Никаких новых улучшений, идей, подфаз.
4. **Pro (QA, APPROVE)** — выводит:
   - `APPROVED`
   - Список git-команд (add, commit, push, tag)
   - `PROMPT FOR PRO (NEXT PHASE)` для планирования следующей подфазы.
5. **Все три блока обязательны.** Пропуск любого — нарушение workflow.
6. **Пользователь только копирует блоки между сессиями.** Не пишет запросы вручную.
7. **PROMPT FOR FLASH** содержит только:
   - Goal
   - Allowed Files
   - Forbidden Files
   - Tasks
   - Definition of Done
   - Stop Condition
   
   Без повторного объяснения архитектуры, истории проекта или уже описанных правил.
