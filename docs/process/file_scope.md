# File Scope — White Lists

## Purpose

Define explicit white lists of allowed files for each task type.
The agent MUST NOT read files outside the allowed list.

## Task Type → Allowed Files

### Documentation

```
docs/process/*
docs/PROJECT_CONVENTIONS.md
AGENTS.md
README.md
```

### QA / Regression Tests

```
docs/process/qa.md (future)
tests/<matching_test_file>
src/<matching_module>
docs/DEFINITION_OF_DONE.md
```

### Architecture Review

```
docs/ARCHITECTURE_DECISIONS.md
docs/ENGINEERING_PLAYBOOK.md
docs/PROJECT_STATE.md
src/<matching_module>
```

### Business Configuration

```
clients/<client_name>/*
```

### Python Bug Fix

Only the failing module and its test:

```
src/<buggy_module>/
tests/<corresponding_test_file>
```

No README. No AGENTS. No unrelated docs.

### Code Review (Pro)

```
src/<changed_files>
tests/<changed_tests>
docs/PROJECT_CONVENTIONS.md
docs/DEFINITION_OF_DONE.md
```

### Phase Planning (Pro only)

```
docs/PROJECT_STATE.md
docs/ARCHITECTURE_DECISIONS.md
docs/BACKLOG.md
docs/DEFINITION_OF_DONE.md
clients/<client_name>/*
```

### New Phase Implementation (Flash)

Only the files listed in the architecture plan. Nothing else.

### Handoff (любая роль)

Тип `handoff` означает, что модель получила готовый блок `PROMPT FOR <роль>`.
Allowed Files определяются содержимым этого блока. Агент **не выполняет** классификацию,
а сразу переходит к чтению файлов, указанных в блоке.