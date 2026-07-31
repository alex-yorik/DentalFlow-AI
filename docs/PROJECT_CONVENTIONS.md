# Project Conventions

## Communication
- All progress reports, explanations, and questions to the developer must be in Russian.
- Source code, identifiers, filenames, JSON keys, and Git commit messages stay in English.

## Workflow
- Complete one phase at a time.
- Stop after each phase and wait for approval.
- Commit and push after each approved phase.
- Update PROJECT_STATE.md after each approved phase.

## Stability Rules
- Do not change completed phases unless there is a clear reason.
- Do not move business logic back into Telegram handlers.
- Do not hardcode client-specific text in Python.
- Keep configuration-driven behavior in client JSON files.

## Development Workflow (Mandatory)

Every phase MUST follow this sequence:

1. **Planning** — Pro scopes the phase.
2. **Architecture Plan** — Pro writes the plan.
3. **Implementation** — Flash implements.
4. **Code Review** — Pro reviews.
5. **Fixes** — Flash fixes findings.
6. **Regression Tests** — Flash writes tests for every fix.
7. **QA Verification** — Pro re-checks only the original findings and new tests.
8. **APPROVE / REQUEST_CHANGES** — Pro decides.
   - On APPROVE: merge, commit, push, git tag, close phase.
   - On REQUEST_CHANGES: return to step 5.

Key rules:
- Flash **always** writes regression tests after fixing findings.
- Pro **never** searches for new issues during re-review — only verifies previous findings.
- After APPROVE, no new ideas are applied to the current phase. They go to `docs/BACKLOG.md`.
