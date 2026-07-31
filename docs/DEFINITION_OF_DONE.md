# Definition of Done

A phase is considered complete **only** when ALL of the following conditions are met.

## Checklist

- [ ] Functionality implemented according to the architecture plan
- [ ] Code passes architecture / code review (Pro)
- [ ] All review findings are fixed
- [ ] Regression tests are written for every fixed finding
- [ ] All tests pass (`pytest tests/ -q`)
- [ ] Documentation is updated (PROJECT_STATE.md, AGENTS.md, etc.)
- [ ] APPROVE verdict received from Pro
- [ ] Merge completed
- [ ] Commit created
- [ ] Push to remote
- [ ] Git tag created
- [ ] PROJECT_STATE.md updated with new phase status

## After Done

- No new features may be added to the completed phase.
- New ideas go to `docs/BACKLOG.md`.
- The next phase begins.