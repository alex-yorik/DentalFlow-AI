# Context Policy — Progressive Context Loading

## Purpose

Minimize token usage by loading only the minimum context required for each task.

## Loading Sequence

```
Task Received
       │
       ▼
1. Classify task type
   (docs/process/task_classifier.md)
       │
       ▼
2. Determine Allowed Files
   (docs/process/file_scope.md)
       │
       ▼
3. Read only Allowed Files
       │
       ▼
4. Stop reading as soon as sufficient
   information is obtained
       │
       ▼
5. Implement
       │
       ▼
6. Stop
```

## Rules

### Must Do
- Classify the task before opening any file
- Open only files from the Allowed Files list
- Stop reading immediately when the task is understood
- Use targeted reads (specific file, specific lines) instead of full-file reads

### Must NOT Do
- **Recursive directory search** — `ls -R`, `tree`, recursive glob without a specific pattern
- **`grep` across the entire project** — restrict search to specific directories or file patterns
- **`find` across the entire project** — use only with a specific path and pattern
- **Read README.md** — unless the task explicitly requires it
- **Read docs/** — unless the task is documentation-related
- **Open files "just in case"** — every opened file must have a stated reason
- **Pre-read files for future tasks** — read only what is needed for the current task

## Rationale

Every unnecessary file read increases token cost.
Progressive loading keeps each session lean and focused.