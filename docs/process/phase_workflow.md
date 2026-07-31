# Phase Workflow

## Purpose

Define the subphase decomposition rule for large phases.
This policy prevents a single expensive session from implementing an entire large phase.

## Rule

**Every Phase MUST be split into subphases.**

A subphase is the smallest unit of work that can be reviewed, approved, and committed independently.

Each subphase follows the full review cycle.

## Example — Phase 7

```
Phase 7 (Polish and Portfolio Readiness)
  ├── 7A — Security Hardening
  ├── 7B — Error Handling Completeness
  ├── 7C — Logging and Observability
  ├── 7D — Documentation and README
  ├── 7E — Tests
  ├── 7F — Code Cleanup
  └── 7G — Docker Verification
```

## Subphase Requirements

Each subphase MUST:

1. **Have a clear scope** — described in 2–3 sentences
2. **Have an Allowed Files list** — max 5 files
3. **Fit in one session** — typically 3–5 files, 1–2 hours of work
4. **End with a commit and push**
5. **Start a new session** after the commit

## Forbidden

- Implementing the entire large Phase in one session
- Merging subphases together
- Skipping review for any subphase
- Combining subphases into a single commit
- **Expanding subphase scope beyond the original plan — split into a new subphase instead**

## Handoff Tokens

Каждая подфаза завершается **token-minimal handoff-блоком**, который пользователь копирует в следующую сессию.

### Типы токенов

| Токен | Кто генерирует | Куда вставляется |
|-------|---------------|-------------------|
| `PROMPT FOR FLASH` | Pro (после Planning) | Сессия Flash |
| `PROMPT FOR PRO QA` | Flash (после Build) | Сессия Pro для QA |
| `PROMPT FOR PRO (NEXT PHASE)` | Pro (после APPROVE) | Сессия Pro для следующей подфазы |

### Формат

```
====================
PROMPT FOR <роль>
====================
<содержание блока>
```

### Правила

1. Каждый токен — законченное задание, которое можно скопировать одним блоком.
2. Пользователь **не редактирует** содержимое блока и **не дописывает** свой запрос.
3. После `REQUEST_CHANGES` — только `PROMPT FOR FLASH`, без дополнительных пояснений.
4. После `APPROVE` — `APPROVED` + git-команды + `PROMPT FOR PRO (NEXT PHASE)`.
5. Токены **обязательны**. Пропуск токена — нарушение workflow.