# Master Planning Prompt for DeepSeek V4 Pro

You are working inside an existing Python repository. Your task is not to code features yet. Your task is to analyze the repository, understand what already exists, and produce a production oriented implementation plan for a commercial demo product called DentalFlow AI.

## 1. Your role

You are the architect, planner, security reviewer, and systems designer.

You must:
1. Inspect the current repository structure and existing code.
2. Determine what should be reused, refactored, or preserved.
3. Design a scalable architecture for a portfolio grade AI receptionist and lead automation demo.
4. Separate deterministic business logic from probabilistic LLM behavior.
5. Produce a detailed implementation plan only.

You must not start implementation until the plan is reviewed and explicitly approved.

## 2. Product goal

The product is a commercial MVP demo for an American dental clinic.

The core user flow is:
1. A prospective patient writes in natural English.
2. The AI receptionist answers only from approved clinic data.
3. The AI qualifies the user as a lead when appropriate.
4. The system collects missing lead fields such as name, phone, email, service, urgency, and preferred time.
5. The system applies business rules and safety rules.
6. The system creates or updates the lead in a CRM.
7. The system notifies staff.
8. The system performs follow up if the user does not complete the booking flow.

Telegram is only the first channel. The architecture must allow future channels such as web and WhatsApp without rewriting the core.

## 3. Hard constraints

1. Do not build a tangled chatbot.
2. Do not let prompts replace business logic.
3. Do not let the LLM directly control CRM writes or protected actions.
4. Do not invent prices, availability, medical advice, discounts, or treatment guarantees.
5. Do not assume full autonomy. Every critical action must be validated by Python.
6. Do not over engineer the first MVP with voice AI, payments, multiple CRMs, multiple LLM providers, vector databases, or a large admin panel.
7. Preserve the possibility of a universal reusable template.
8. If an existing JSON based client configuration approach already exists, do not break it. Extend it carefully.

## 4. Required architecture principles

Design the system around these boundaries:

1. Channels layer
   Telegram should only handle transport, message delivery, and user interaction.
   It must not contain business rules.

2. AI layer
   The LLM should perform interpretation, extraction, and structured reasoning.
   It should return structured outputs, not freeform instructions that control the program.

3. Business rules layer
   Deterministic Python logic must validate what the AI wants to do.
   This layer decides whether an action is allowed.

4. Leads layer
   Lead data should have explicit models and a clear lifecycle.

5. Integrations layer
   CRM, notifications, and future calendar integrations must go through provider interfaces.

6. Follow up layer
   Follow up must be a separate workflow component, not buried inside chat handlers.

7. Storage layer
   Storage must be isolated and replaceable.

8. Config layer
   Client specific behavior must live in config files and data files as much as possible.

## 5. What you must analyze

Inspect the repository and answer these questions:
1. What is the current project structure?
2. Which modules already support reuse?
3. Where is the architecture currently mixed or unclear?
4. What should remain stable across clients?
5. What should be made configurable per client?
6. What can be refactored without breaking the existing bot or template?
7. What are the main risks in the current codebase?
8. What tests already exist and what is missing?
9. What deployment assumptions already exist?
10. What security or operational concerns need attention?

## 6. Domain model you should design

Design a lead lifecycle and a minimal state machine suitable for the demo.

At minimum, think through:
1. New conversation
2. FAQ only
3. Lead identified
4. Missing contact details
5. Qualification in progress
6. Ready for CRM write
7. CRM created or updated
8. Staff notified
9. Follow up pending
10. Follow up sent
11. Closed
12. Do not contact or blocked

You should define the key fields for a lead, such as:
1. Name
2. Phone
3. Email
4. Service
5. Intent
6. Urgency
7. Preferred time
8. Source
9. Qualification status
10. Conversation summary
11. Consent or opt in state where relevant
12. Internal tags

## 7. Structured AI output

Design the AI contract so that the model returns structured data.

The AI should be able to express things like:
1. intent
2. confidence
3. extracted fields
4. missing fields
5. suggested next action
6. whether the user is a lead
7. whether the request is safe or unsafe
8. whether CRM write is allowed
9. whether follow up should be scheduled

The AI must not directly perform actions. It should propose structured decisions. Python must validate them.

## 8. Safety and business rules

You must design a rules system that clearly defines what the AI may and may not do.

At minimum, the plan should cover:
1. Answering FAQ from approved data
2. Explaining services from approved data
3. Collecting contact details
4. Qualifying leads
5. Offering approved appointment slots if validated by the system
6. Refusing unsupported medical claims
7. Refusing invented availability
8. Refusing invented prices
9. Refusing diagnosis or treatment promises
10. Blocking unsafe or invalid requests

You should also define how the system handles:
1. Low confidence outputs
2. Conflicting user data
3. Missing critical fields
4. Repeated user messages
5. Out of scope questions
6. Escalation to human staff

## 9. CRM abstraction

Design a provider interface for CRM integrations.

At minimum, define methods conceptually for:
1. create_contact
2. update_contact
3. create_lead
4. add_note
5. update_stage

The architecture must support a mock CRM for testing and one real CRM for the portfolio demo, but it must remain easy to extend later.

Do not hardwire the application to a specific CRM in the core logic.

## 10. Notifications and follow up

Design the follow up engine as a separate subsystem.

The follow up system should support:
1. Scheduled follow up after incomplete lead capture
2. Demo mode with short delays for presentations
3. Cancellation if the lead is completed or closed
4. Clear state tracking so repeated follow ups do not happen incorrectly

The plan should specify how follow up tasks are stored, triggered, retried, and stopped.

## 11. Configuration strategy

Assume a reusable client based configuration layout.

Design a config structure that can support files such as:
1. business.json
2. services.json
3. faq.json
4. rules.json
5. qualification.json
6. followup.json

You should define what each file is responsible for and what data belongs there.

The plan must preserve the universal template idea, where a new client can be onboarded mostly by replacing config and media, not by rewriting Python.

## 12. Testing strategy

You must propose a practical testing plan for the MVP.

At minimum, include:
1. Unit tests for rules and lead state transitions
2. Unit tests for structured AI output validation
3. Unit tests for CRM provider interfaces using a mock provider
4. Integration tests for the main conversation flow
5. Follow up tests
6. Negative tests for invalid or unsafe AI outputs
7. Regression tests for config driven client behavior

## 13. Security and reliability review

You must assess:
1. Prompt injection risk
2. Unsafe action risk
3. Data leakage risk
4. Invalid CRM write risk
5. Follow up duplication risk
6. Channel specific failure modes
7. Logging and audit needs
8. Environment variable and secret handling
9. Deployment fragility
10. Basic observability needs

## 14. Deliverable

Your only deliverable for this stage is an `IMPLEMENTATION_PLAN.md` file.

That document must include:
1. A concise architecture summary
2. Current repository assessment
3. Proposed module structure
4. Lead state machine
5. AI contract shape
6. Business rules strategy
7. CRM abstraction plan
8. Follow up engine plan
9. Config strategy
10. Testing strategy
11. Security and risks
12. Step by step implementation phases
13. A clear list of out of scope items for v1

## 15. Output requirements

Your response must be structured, practical, and explicit.

Use this format:
1. Executive summary
2. Repository findings
3. Proposed architecture
4. Data and state model
5. Safety and business rules
6. Integrations
7. Follow up engine
8. Config and client onboarding
9. Test plan
10. Risks and mitigations
11. Implementation phases
12. Open questions
13. IMPLEMENTATION_PLAN.md content outline

Be specific. Do not write vague advice.

## 16. Final instruction

Do not implement code yet.

Do not begin writing application files yet.

Do not refactor without first explaining the reason.

Do not assume missing context without stating it.

Your next output should be the implementation plan only.
