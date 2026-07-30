# DentalFlow AI Project Rules

## Goal
Build a production-oriented portfolio MVP for an AI receptionist and lead automation system.

## Core Principles
- Preserve working code unless a change is clearly needed.
- Keep changes small and isolated.
- Separate channels, AI logic, business rules, storage, and integrations.
- AI proposes, Python validates and decides.
- Use configuration files for client-specific behavior whenever possible.
- Do not invent prices, availability, medical advice, or guarantees.
- Do not let the LLM write directly to protected systems.

## Architecture Expectations
- Telegram is only the first channel.
- The core must later support web and WhatsApp without rewrites.
- Lead handling must be a state machine.
- CRM access must go through provider interfaces.
- Follow-up must be a separate subsystem.

## Working Style
- First analyze, then plan, then implement.
- If requirements are unclear, ask instead of guessing.
- Keep documentation and code aligned.
