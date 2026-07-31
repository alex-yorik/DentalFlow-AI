# Review Policy — QA Workflow

## Purpose

Define the exact QA workflow after REQUEST CHANGES and APPROVE.
Prevent endless review loops and scope expansion after approval.

## Workflow After REQUEST CHANGES

```
Pro: REQUEST CHANGES
       │
       ▼
[PROMPT FOR FLASH]  ← только перечень исправлений, без новых улучшений
       │
       ▼
Flash: fixes all noted findings
       │
       ▼
Flash: adds regression tests for every fix
       │
       ▼
Pro: re-checks ONLY:
     • Are the original findings fixed?
     • Are the new regression tests meaningful?
     • Do all tests pass?
       │
       ├── APPROVE → [PROMPT FOR PRO (NEXT PHASE)]
       └── REQUEST CHANGES → repeat (max 1 additional cycle)
```

## Rules After REQUEST CHANGES

- Pro выводит **только** блок `PROMPT FOR FLASH` с перечнем исправлений.
- Pro **не ищет** новые улучшения, новые идеи, новые подфазы.
- Pro **не добавляет** ничего сверх списка исправлений.
- Flash фиксирует **только указанные** замечания — никакой дополнительной работы.
- Flash пишет регрессионные тесты **только** для исправленных замечаний.
- Максимум 2 цикла ревью на подфазу.

## Workflow After APPROVE

```
Pro: APPROVE
       │
       ▼
Вывод:
  • APPROVED
  • git add <files>
  • git commit -m "<message>"
  • git push
  • git tag <version>
       │
       ▼
[PROMPT FOR PRO (NEXT PHASE)]  ← планирование следующей подфазы
       │
       ▼
Пользователь копирует блок в новую сессию Pro
```

## Rules After APPROVE

- Pro **обязан** вывести:
  1. `APPROVED`
  2. Список git-команд для коммита, пуша и тэга
  3. Блок `PROMPT FOR PRO (NEXT PHASE)` для запуска следующей подфазы
- Запрещён поиск новых улучшений, техдолга, рефакторинга.
- Запрещено расширение scope текущей подфазы.
- Запрещено начинать новый architecture review или QA review.
- Все новые идеи → в `docs/BACKLOG.md`.

## One Subphase = One Review Cycle

Each subphase enters review **once**.
After the second review cycle, the reviewer must either APPROVE or clearly explain why the phase cannot proceed. Blockers must be actionable.