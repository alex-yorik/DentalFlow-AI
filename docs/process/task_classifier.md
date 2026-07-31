# Task Classifier

## Purpose

Before any file is read, the agent must determine what type of task it is executing.
The classifier output determines the allowed file scope.

## Algorithm

```
User Request
       │
       ▼
Classifier
       │
       ├── handoff          → docs/process/file_scope.md
       ├── documentation    → docs/process/file_scope.md
       ├── qa               → docs/process/file_scope.md
       ├── architecture     → docs/process/file_scope.md
       ├── configuration    → docs/process/file_scope.md
       ├── bug_fix          → docs/process/file_scope.md
       ├── code_review      → docs/process/file_scope.md
       ├── phase_planning   → docs/process/file_scope.md
       └── new_phase        → docs/process/file_scope.md
```

## Classification Heuristics

| If request contains … | Classify as … |
|-----------------------|---------------|
| "PROMPT FOR", "handoff block", "next phase" | `handoff` |
| "documentation", "doc", "readme", "playbook" | `documentation` |
| "test", "regression", "qa", "verify" | `qa` |
| "architecture", "review", "design" | `architecture` |
| "config", "json", "client", "business" | `configuration` |
| "bug", "error", "fix", "broken" | `bug_fix` |
| "code review", "approve", "changes" | `code_review` |
| "phase", "planning", "scope" | `phase_planning` |
| "implement", "build", "new" | `new_phase` |

If the type is ambiguous, default to `bug_fix` and request clarification from the architect.