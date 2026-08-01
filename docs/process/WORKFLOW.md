# Development Workflow

## Task Types
| Type | Keywords | Allowed Files |
|------|----------|---------------|
| bug_fix | "bug", "error", "fix", "broken" | src/<module>/, tests/<test> |
| feature | "implement", "build", "new", "add" | src/<module>/, tests/<test>, clients/ |
| docs | "documentation", "doc", "readme" | docs/, README.md, AGENTS.md |
| qa | "test", "regression", "verify", "qa" | tests/, src/<changed> |
| config | "config", "json", "client", "business" | clients/<client>/* |
| architecture | "architecture", "review", "design" | docs/architecture.md, docs/ARCHITECTURE_DECISIONS.md |

## Core Rules
1. **One task = max 5 files** (excluding docs/process/* for doc tasks)
2. **Classify task by keywords** (use table above)
3. **Read ONLY Allowed Files** for your task type
4. **Stop reading** when task is understood
5. **No speculative reading** - never open files "just in case"

## Workflow

### Planning (Pro)
- Create max 5 phases
- Each phase: max 3 tasks
- Each task: 2-3 sentences, list exact files

### Implementation (Flash)
- Implement ONE task at a time
- Work only within Allowed Files
- Stop after task completion

### Review (Pro)
- APPROVE → git commit → next task
- REQUEST CHANGES → fix ONLY noted issues
- Max 2 review cycles per task

## Handoff Protocol

After each task, generate minimal prompt for next role:

### PROMPT FOR FLASH
- Goal (1 sentence)
- Allowed Files (list)
- Forbidden Files (list)
- Tasks (bullet points)
- Definition of Done (checklist)
- Stop Condition (1 sentence)

### PROMPT FOR PRO QA
- Changed files (list)
- What to verify (checklist)
- Expected result (1-2 sentences)

### PROMPT FOR NEXT PHASE
- Completed context (2-3 sentences)
- Next phase goal (1 sentence)
- Key constraints (if any)

## Rules After REQUEST CHANGES
- Pro outputs ONLY list of fixes
- No new improvements, ideas, or scope expansion
- Flash fixes ONLY noted findings
- Flash adds regression tests for each fix
- Max 2 cycles

## Rules After APPROVE
- Pro outputs:
  1. APPROVED
  2. Git commands (add, commit, push, tag)
  3. PROMPT FOR NEXT PHASE
- No new improvements or tech debt search
- All new ideas → docs/BACKLOG.md
## Handoff Format (MANDATORY)

Flash MUST output ONLY:
1. Changed files (list with +/- counts)
2. What to verify (3-5 bullet points)
3. Expected result (1-2 sentences)

Flash MUST NOT output:
- Detailed tables with 20+ rows
- Code structure diagrams
- Full DoD checklists
- Backlog tables
- Questions to reviewer
- Git diff summaries

Maximum handoff length: 20 lines.

## PROMPT FOR FLASH Format (CRITICAL)

When generating PROMPT FOR FLASH, Planner MUST keep it SHORT:

**Maximum length: 25-30 lines**

**Required sections:**
- ROLE: developer
- PHASE: [phase name]
- Allowed Files: [list, max 6]
- Goal: [1 sentence]
- DoD: [3-5 bullet points]
- Rules: [2-3 critical constraints only]
- Start → py_compile → pytest → PROMPT FOR PRO QA

**FORBIDDEN:**
- Code examples (Flash will figure it out)
- Detailed analysis of options
- Step-by-step implementation instructions
- "Key rules" sections with 8+ items
- Warnings like "ВНИМАНИЕ", "СТОП"

**Rationale:** Flash is cheap ($0.01-0.02), Pro is expensive ($0.05-0.10).
Don't do Flash's work in Pro's prompt.

