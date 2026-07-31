# Master Planning Prompt (v2 - Simplified)

## 1. Your Role

You are the architect and planner for DentalFlow-AI.

Your task: Analyze the repository and create a step-by-step implementation plan.

Your constraints:
- Analyze FIRST, then plan
- Do NOT implement code
- Do NOT refactor without explanation
- Keep it practical and specific

## 2. Project Context

Product: AI receptionist for American dental clinic (Telegram bot MVP)

Core flow:
1. Patient writes in natural English
2. AI answers from approved clinic data only
3. AI qualifies user as lead when appropriate
4. System collects missing lead fields (name, phone, email, service, urgency, preferred time)
5. System applies business rules and safety rules
6. System creates/updates lead in CRM
7. System notifies staff
8. System performs follow-up if user doesn't complete booking

Hard constraints:
- Do NOT build a tangled chatbot
- Do NOT let LLM directly control CRM writes
- Do NOT invent prices, availability, medical advice
- Every critical action MUST be validated by Python
- Telegram is first channel (later: web, WhatsApp without rewrites)

## 3. What You Must Analyze

Inspect the repository and answer these questions:

### Current State
1. What is the current project structure?
2. Which modules already support reuse?
3. Where is the architecture currently mixed or unclear?
4. What tests already exist and what is missing?

### Design Requirements
5. Design a lead lifecycle state machine (states: new, FAQ, identified, qualification, CRM write, notified, follow-up, closed)
6. Design structured AI output contract (intent, confidence, extracted fields, missing fields, suggested action)
7. Design business rules system (what AI may/may not do)
8. Design CRM provider interface (create_contact, update_contact, create_lead, add_note, update_stage)
9. Design follow-up engine (scheduled reminders, demo mode, cancellation, state tracking)
10. Design configuration strategy (JSON files per client: business.json, services.json, faq.json, rules.json, qualification.json, followup.json)

## 4. Output Format

Your output MUST follow this exact structure:

### Part A: Architecture Assessment (max 500 words)

Current Structure (3 bullet points)
- What exists
- What works well
- What needs refactoring

Repository Findings (5 bullet points)
- Key modules found
- Reusable components
- Problem areas
- Test coverage status
- Deployment assumptions

### Part B: Proposed Architecture (max 800 words)

Module Structure (tree format):
src/
  channels/telegram/ (thin handlers - transport only)
  llm/ (structured output, parsing)
  rules/ (business rules validation)
  leads/ (state machine, models)
  integrations/ (CRM provider interface)
  followup/ (background async engine)
  storage/ (SQLite database layer)
  config/ (JSON config loader)

Key Decisions (5 bullet points)
- Lead state machine design
- AI contract shape
- CRM abstraction approach
- Follow-up engine design
- Configuration strategy

### Part C: Implementation Plan (max 600 words)

Phase 1: Foundation (Week 1)
- Task 1.1: [Description, 2-3 sentences] | Files: [list exact files]
- Task 1.2: [Description, 2-3 sentences] | Files: [list exact files]
- Task 1.3: [Description, 2-3 sentences] | Files: [list exact files]

Phase 2: Core Features (Week 2)
- Task 2.1: [Description] | Files: [list]
- Task 2.2: [Description] | Files: [list]
- Task 2.3: [Description] | Files: [list]

Phase 3: Integrations (Week 3)
- Task 3.1: [Description] | Files: [list]
- Task 3.2: [Description] | Files: [list]

Phase 4: Follow-up and Notifications (Week 4)
- Task 4.1: [Description] | Files: [list]
- Task 4.2: [Description] | Files: [list]

Phase 5: Polish and Testing (Week 5)
- Task 5.1: [Description] | Files: [list]
- Task 5.2: [Description] | Files: [list]

Out of Scope for v1 (3 bullet points)
- What is explicitly NOT included

## 5. Output Requirements

Your response must be:
- Structured (use exact sections above)
- Practical (no vague advice)
- Specific (exact file names, exact states, exact methods)
- Concise (max 2000 words total)

Do NOT:
- Write long explanations
- Repeat existing architecture decisions
- Include implementation code
- Describe obvious things

Do:
- Focus on what's missing or needs refactoring
- Provide actionable next steps
- List exact files to create/modify
- Specify clear acceptance criteria

## 6. Final Instruction

Your next output should be the implementation plan ONLY.

Do NOT start implementation. Do NOT write application code.

Produce the plan in the exact format specified in Section 4.