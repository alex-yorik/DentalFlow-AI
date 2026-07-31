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