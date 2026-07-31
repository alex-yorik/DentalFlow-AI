# Scope Policy

## Purpose

Prevent scope creep and runaway context size.
Every task must fit within a strict file limit.

## Hard Limit

**One task = maximum 3–5 files.**

This includes:
- Source files to read
- Source files to modify
- Test files to read or modify
- Configuration files to read or modify

Documentation files (docs/process/*) are excluded from the limit only when the task is documentation-related.

## Enforcement

| Role | Rule |
|------|------|
| **Pro (Architect)** | If a task requires more than 5 files, Pro MUST split it into smaller subtasks. |
| **Flash (Developer)** | Flash MUST NOT expand scope beyond the Allowed Files list. If a needed file is not in the list, Flash MUST stop and ask Pro. |

## Consequences

- If Flash reads a file outside Allowed Files — the task is rejected at review.
- If Flash modifies a file outside Allowed Files — the change is reverted.
- If a task grows beyond 5 files mid-implementation — Flash stops and requests re-scoping.

## Allowed Files Priority

1. Only the files explicitly listed for the task
2. Documentation process files (`docs/process/*`) — only for process tasks
3. No other files without explicit permission