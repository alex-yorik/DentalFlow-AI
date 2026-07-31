# DentalFlow AI

AI Receptionist & Lead Automation Framework.

DentalFlow AI is a production-grade portfolio MVP that demonstrates how an AI-powered virtual receptionist can handle clinic inquiries, qualify leads, integrate with CRM, and run follow-up campaigns — all without hardcoded business logic.

---

## Features

- **AI Receptionist** — answers FAQs about hours, location, services, insurance using client config
- **Lead Qualification** — collects name, phone, service interest; scores and routes leads automatically
- **State Machine** — explicit finite state machine governs lead lifecycle from `new` to `closed`
- **CRM Integration** — provider interface pattern; ships with a mock provider, ready for HubSpot/Salesforce
- **Follow-up Engine** — background asyncio task sends multi-step reminders with configurable delays and retries
- **Safety Guards** — blocks pricing/diagnosis/prescription requests, enforces refusal limits, falls back to safe defaults
- **Multi-channel Ready** — Telegram is the first transport; handlers are thin, core logic is reusable
- **Configuration-driven** — every clinic-specific value lives in JSON files, not Python

---

## Architecture

```
User (Telegram)
     │
     ▼
┌─────────────────┐
│  Telegram Handler│  (thin — parse & delegate)
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   Rules / Safety │────▶│   LLM (OpenAI)  │
│   validator      │     │   structured     │
│   blocked phrases│     │   output only    │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  Lead State     │     │  Conversation   │
│  Machine        │     │  Summary Store  │
│  (qualification)│     │  (AIOSQLite)    │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  CRM Provider   │     │  Follow-up      │
│  Interface      │     │  Engine         │
│  (mock / future)│     │  (async polling)│
└─────────────────┘     └─────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Framework | python-telegram-bot 20.x |
| AI | OpenAI API (structured output with Pydantic) |
| Database | SQLite via aiosqlite |
| Validation | Pydantic v2 |
| Container | Docker + docker-compose |
| Testing | pytest, pytest-asyncio |

---

## Quick Start

### Local

```bash
# 1. Clone the repository
git clone <repo-url>
cd DentalFlow-AI

# 2. Set up environment
cp .env.example .env
# Edit .env — add TELEGRAM_BOT_TOKEN and OPENAI_API_KEY

# 3. Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Run
python -m src.main
```

### Docker

```bash
docker-compose up -d
docker-compose logs -f --tail=30
```

---

## Demo Guide

1. **Create a Telegram bot** — talk to [@BotFather](https://t.me/BotFather), run `/newbot`, save the token.
2. **Set the token** — add `TELEGRAM_BOT_TOKEN=...` to `.env`.
3. **Set OpenAI key** — add `OPENAI_API_KEY=...` and optionally change `OPENAI_MODEL` (default: `gpt-4o-mini`).
4. **Start the bot** — `python -m src.main` or `docker-compose up -d`.
5. **Test the flow**:
   - Say *"Hi"* — bot welcomes you
   - Ask *"What are your hours?"* — FAQ answer
   - Say *"I'd like to book a checkup"* — lead collection begins
   - Provide name and phone — qualification scores and routes to CRM

---

## Project Structure

```
DentalFlow-AI/
├── src/                    # Core application
│   ├── channels/           # Transport layer (Telegram handler)
│   ├── config/             # Configuration loader
│   ├── followup/           # Follow-up engine
│   ├── integrations/       # CRM provider interface + mock
│   ├── leads/              # Lead state machine + repository
│   ├── llm/                # OpenAI client + contract models
│   ├── rules/              # Safety, validation, FAQ routing
│   ├── storage/            # SQLite database layer
│   └── main.py             # Entry point
├── clients/                # Business configuration
│   └── demo_dental/        # Demo clinic (JSON configs)
├── tests/                  # Unit + integration tests
│   ├── unit/
│   └── integration/
├── docs/                   # Documentation
└── data/                   # Runtime data (SQLite DB)
```

---

## Planning

Use `docs/prompts/master-planning-prompt-v2.md` for architecture planning (simplified version).

---

## License

MIT — see LICENSE file.