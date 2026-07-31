# Review Policy — QA Workflow

## Purpose

Define the exact QA workflow after REQUEST CHANGES and APPROVE.
Prevent endless review loops and scope expansion after approval.

## Workflow After REQUEST CHANGES

```
Pro: REQUEST CHANGES
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
       ├── APPROVE → see below
       └── REQUEST CHANGES → repeat (max 1 additional cycle)
```

## Rules After REQUEST CHANGES

- Pro reviews **only** the original findings
- Pro does **not** search for new issues
- Pro does **not** introduce new findings unless they block merge
- Flash fixes **only** the specified findings — no extra work
- Flash writes regression tests **only** for the fixed findings
- Maximum 2 review cycles per subphase

## Workflow After APPROVE

```
Pro: APPROVE
       │
       ▼
Merge immediately
       │
       ▼
Commit
       │
       ▼
Push
       │
       ▼
New session
```

## Forbidden After APPROVE

- Searching for new improvements
- Searching for new technical debt
- Proposing new refactoring
- Expanding scope
- Starting another architecture review
- Starting another QA review
- Adding new ideas to the current subphase (go to BACKLOG.md)

## One Subphase = One Review Cycle

Each subphase enters review **once**.
After the second review cycle, the reviewer must either APPROVE or clearly explain why the phase cannot proceed. Blockers must be actionable.