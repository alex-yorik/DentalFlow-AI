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
