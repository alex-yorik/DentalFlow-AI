# Progressive Context Loading

## Purpose

Reduce OpenCode operating costs by strictly limiting the amount of context loaded during a task.
The agent must never read files it does not need.

## Strategy

```
Zero Context Start
       │
       ▼
Classify Task Type
       │
       ▼
Determine Minimal File List
       │
       ▼
Open Only Listed Files
       │
       ▼
Enough Information?
      ├── YES → Stop Reading Immediately
      └── NO  → Request One Additional File → Return to Check
```

## Rules

### Rule 1 — Zero Context Start

Every task starts with no pre-loaded files. The agent does not automatically read AGENTS.md, README.md, or any documentation.

### Rule 2 — Classify First

Before opening any file, the agent must classify the task type (see `docs/process/task_classifier.md`).

### Rule 3 — Minimal File List

Based on the task type, determine the minimal set of files needed. Never add files "just in case".

### Rule 4 — Open Only Listed Files

Open only files on the allowed list. One at a time if possible.

### Rule 5 — Stop Reading Early

If the currently loaded information is sufficient to complete the task, stop reading. Do not open additional files.

### Rule 6 — Request, Don't Explore

If more information is needed, the agent must explicitly name the single missing file and explain why it is required. The request is approved or denied by the architect.

### Rule 7 — No Speculative Reading

Never open supplementary documentation in advance. Never scan directories recursively.