# Engineering Playbook

## Purpose

This document defines the standard engineering process for the DentalFlow AI project.
It governs how phases are planned, implemented, reviewed, approved, and closed.
Every team member and every AI agent participating in this project MUST follow this playbook.

## Team Roles

### Architect (DeepSeek V4 Pro)

**Tag:** `architect` / `Pro`

**Responsibilities:**
- Architecture design and planning
- Phase scoping and technical direction
- Code review of implementation
- QA review of regression tests
- Final approval (APPROVE / REQUEST CHANGES)

### Developer (DeepSeek V4 Flash)

**Tag:** `developer` / `Flash`

**Responsibilities:**
- Implementation of planned phases
- Fixing review findings from Pro
- Writing regression tests for every fix
- Running tests and reporting results
- Documentation updates

### External Reviewer (ChatGPT)

**Tag:** `reviewer` / `External`

**Responsibilities:**
- Architecture consulting on request
- Process validation
- Engineering guidance
- Independent review for critical decisions

---

## Standard Development Workflow

Every phase follows this exact sequence:

```
Phase Planning
       │
       ▼
Architecture Plan (Pro)
       │
       ▼
Implementation (Flash)
       │
       ▼
Architecture / Code Review (Pro)
       │
       ▼
Fixes (Flash)
       │
       ▼
Regression Tests (Flash)
       │
       ▼
QA Verification (Pro)
       │
       ▼
APPROVE
       │
       ▼
Merge
       │
       ▼
Commit
       │
       ▼
Push
       │
       ▼
Git Tag
       │
       ▼
Next Phase
```

**No step may be skipped.**  
**No step may be reordered.**

## Context Loading Order

Every implementation task follows this sequence to minimize context:

```
Task
  │
  ▼
Allowed Files
  │
  ▼
Read
  │
  ▼
Implement
  │
  ▼
Test
  │
  ▼
Stop
```

- Before reading, the agent consults `docs/process/file_scope.md` for the allowed file list.
- The agent reads only files on the list.
- As soon as sufficient information is gathered, reading stops.
- After implementation, the agent runs tests and stops.

See `docs/process/context_loading.md` for the full strategy.

## Cost Optimization Principles

| Principle | Description |
|-----------|-------------|
| **Minimum Context First** | Start with zero files. Add only what is strictly needed. |
| **One File Better Than Five** | A single file is cheaper than five. Prefer reading one file well. |
| **Stop Reading Early** | As soon as the task is understood, close all files. |
| **Never Explore Without Permission** | Do not scan directories or open files "just to see". |
| **Read Only What You Modify** | If the task changes one module, read only that module and its tests. |
| **White-list Before Reading** | Always determine the allowed file list before opening anything. |

These principles reduce agent operating costs by limiting context size to the absolute minimum required for each task.

## Engineering Principles

1. **Configuration over hardcode** — All client-specific values go into JSON files, never into Python code.

2. **Business configuration outside Python** — Business texts, clinic info, service lists, templates live in `clients/<name>/`.

3. **Business logic outside transport layer** — Telegram handlers only route messages. All decisions belong in `src/rules/`, `src/leads/`, etc.

4. **Every bug fix requires regression tests** — No exception. If a test catches it in the future, the fix is complete.

5. **All state transitions go through State Machine** — `apply_transition` is never called without prior `validate_transition`.

6. **Every review finding must be verified** — After fixes, Pro re-checks only the original findings. No new issues are sought.

7. **One phase = one review cycle** — A phase enters review once. If APPROVED it closes. If REQUEST_CHANGES, fixes are made, then a single re-review, then final verdict.

8. **Finished means APPROVED, not perfect** — Excellence is achieved by completing all phases, not by polishing one indefinitely.

9. **Documentation is part of the product** — All docs must stay in sync with code. A docs-only update counts as work.

10. **Avoid endless review loops** — After the second review cycle, the reviewer must either APPROVE or clearly explain why the phase cannot proceed. Blockers must be actionable, not aspirational.

---

## QA Policy

### After the first QA Review

1. **Flash** fixes all noted findings.
2. **Flash** writes regression tests that prove each finding is resolved.
3. **Pro** re-checks only:
   - Whether each finding is fixed
   - Whether each new regression test is meaningful
   - Whether all tests pass

### If verdict = APPROVE

- Review cycle **immediately ends**.
- No additional improvements are searched.
- No new architecture reviews are started.
- No new QA reviews are started.
- Merge is performed.
- Commit, push, git tag.
- Phase is closed.

### If verdict = REQUEST_CHANGES

- Flash fixes the specific findings.
- Flash updates or adds tests.
- Pro re-reviews **only the same findings**.
- No new findings may be introduced at this stage unless they block merge.

### After APPROVE

All ideas that arise after APPROVE are **not** applied to the current phase.
They are recorded in `docs/BACKLOG.md` for future consideration.