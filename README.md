# DentalFlow AI

[![CI](https://github.com/alex-yorik/DentalFlow-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/alex-yorik/DentalFlow-AI/actions/workflows/ci.yml)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)
![License](https://img.shields.io/badge/license-All%20rights%20reserved-red)

AI-powered dental clinic receptionist and lead qualification system. A Telegram bot communicates with patients as a virtual front-desk assistant: it answers questions about services and hours, collects contact details, qualifies leads with a scoring engine, and hands them off to a CRM. All business logic lives in per-client JSON configuration, so the bot can be reconfigured for a different clinic without touching the code.

Demo configuration — the **Bright Smile Dental** clinic (demo client `demo_dental`).

## Features
- **AI receptionist** — answers questions about hours, address, services, and FAQ based on the client configuration
- **Lead qualification** — collects name, phone, and service interest; a scoring engine (rules + points) determines lead readiness for booking (e.g. name +10, phone +10, new-appointment intent +10 = 30 ≥ threshold 25 → the lead is written to CRM; see `clients/demo_dental/qualification.json`)
- **Lead state machine** — an explicit finite-state machine for the lead lifecycle from `new` to `closed`
- **CRM integration** — provider interface with a bundled mock provider (ready for HubSpot/Salesforce)
- **Follow-up engine** — background reminders with configurable delays and retries
- **Conversation safety** — blocks restricted topics (prices, diagnoses, prescriptions), refusal limit, safe default responses
- **Web channel** — the same message processor is exposed via FastAPI (Telegram is the first channel; the architecture supports web/WhatsApp)
- **Monitoring and backups** — watchdog, heartbeat, Telegram alerts, scheduled database backups

## Demo Dialogue

Real transcript from a live session against the Bright Smile Dental demo configuration (synthetic data, PII masked).

**Patient:** Hi! Do you accept new patients?
**Bright Smile Dental:** Yes, Bright Smile Dental accepts new patients! If you're interested in scheduling an appointment, I can help you with that.
**Patient:** I would like to book a teeth cleaning.
**Bright Smile Dental:** Great! I can help you with that. Could you please provide your name and phone number so we can check availability and confirm your appointment?
**Patient:** Patient, +7 999 ***-**-11.
**Bright Smile Dental:** Thank you, Patient! I have your name and phone number. Now, could you please let me know your preferred date and time for the teeth cleaning appointment?
**Patient:** Saturday morning works for me.
**Bright Smile Dental:** I understand that Saturday morning works for you. However, please note that we are closed on Saturdays. Could you provide an alternative date or time for your teeth cleaning appointment?
**Patient:** Then Monday at 10am.
**Bright Smile Dental:** Thank you, Patient! I have noted your preferred time for a teeth cleaning appointment on Monday at 10 AM. We will check availability and confirm with you shortly.

## Tech Stack
- Python 3.12, async/await
- python-telegram-bot 20.x (Telegram channel)
- FastAPI + Uvicorn (web channel), Nginx (proxy + rate limiting)
- OpenAI API (structured output with Pydantic)
- SQLite (aiosqlite, WAL) + Alembic (migrations)
- Pydantic v2 (config validation)
- Docker + docker-compose
- pytest / pytest-asyncio (tests), ruff / mypy (linting and typing)

## Architecture

The project is split into isolated subsystems (`src/`); each process is a separate entrypoint in docker-compose:

```
Telegram channel (bot.py) ─┐
Web channel (FastAPI) ─────┼─▶ message_processor ─▶ rules/safety → LLM (OpenAI)
                           │          │
                           ▼          ▼
                    lead state machine   conversation store (SQLite)
                           │
                           ▼
                      CRM provider (interface)
```

Services (docker-compose):
- **telegram** — python-telegram-bot, message intake and processing
- **web** — FastAPI `/api/chat`, `/health`, `/metrics` (behind nginx)
- **followup** — background reminders and follow-up touches
- **watchdog** — service health checks, Telegram alerts
- **backup** — SQLite backups via the sqlite3 backup API
- **nginx** — TLS, security headers, rate limiting

Data: SQLite in `data/` (volume), schema managed by Alembic migrations (`src/storage/alembic`). Client configuration is JSON in `clients/<client>/` (business, services, faq, rules, qualification, followup, prompts). `src/main.py` is a dev-only entrypoint; production runs through dedicated entrypoints.

## Multi-Channel Support

Currently implemented: Telegram (production-ready), WhatsApp Business API (stub).
Architecture supports adding: Slack (Bot API), SMS via Twilio, Facebook Messenger (Meta Business API), Microsoft Teams (Bot Framework).

Channels are isolated entrypoints sharing the same message processor. They use the common `IncomingMessage` contract and `OutgoingAdapter` protocol (`src/channels/base.py`); there is no plugin registry — adding a channel means adding an entrypoint plus an adapter.

## Security
The project passed a full security audit (2026-08-07). Implemented:
- Fail-closed configuration authentication — required variables (`TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`) are verified at startup, no defaults
- Nginx rate limiting: 10 req/min on `/api/chat` (burst=20), 30 req/min on `/health` and `/metrics` (HTTP 429)
- Security headers: `X-Frame-Options: DENY`, `nosniff`, `CSP default-src 'self'`, `server_tokens off`
- Conversation safety: blocked phrases, refusal limit, safe messages by default
- WAL + `busy_timeout=5000` (database locking eliminated)
- Scheduled backups (every 6 h by default) with rotation (7 days by default)
- .dockerignore + .gitignore — `.env`, `data/`, tests, and docs excluded from the Docker image and git
- Multi-container deployment (build → up -d) with zero downtime

All secrets (`TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`) are stored in `.env`, never in code.

## Installation
1. Copy `.env.example` to `.env`
2. Fill in `TELEGRAM_BOT_TOKEN` and `OPENAI_API_KEY` (all other parameters have defaults)
3. `docker-compose up -d`

## Try It Without Telegram

The web channel runs on the same message processor as the bot, so the full flow works without a Telegram token:

```bash
docker compose up -d web nginx
curl -s -X POST http://localhost:80/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"channel_id":"demo-patient-1","text":"Hi! Do you accept new patients?"}'
```

`POST /api/chat` takes `channel_id` (any stable client-side string identifying the conversation) and `text`, and returns `{"reply": "..."}`. Use a new `channel_id` for a fresh conversation; `GET /api/chat/{channel_id}/messages` returns the stored replies.

Only `OPENAI_API_KEY` is required for the web demo — `TELEGRAM_BOT_TOKEN` is needed only by the `telegram` service. If port 80 is busy, set `NGINX_PORT` in `.env` and use that port in the URL.

## Deployment
```bash
docker-compose build && docker-compose up -d
docker-compose logs -f --tail=30
```

After the first deployment: `chown -R <container uid> data/` (otherwise SQLite will open as read-only).

## Tests

The project includes 31 test files (unit + integration):

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Scope & Authorship

This project was designed and implemented entirely by the author:
Telegram bot, FastAPI backend, WhatsApp adapter stub, LLM integration,
lead state machine, CRM provider interface, follow-up engine, monitoring,
tests, and CI/CD.

## Limitations

This is a working prototype. Current limitations include:
- WhatsApp Business API integration is a stub (requires business account)
- CRM provider is mocked (real integration depends on client's CRM)
- LLM responses may require human review for critical decisions
- Does not collect or store medical information; medical topics are blocked by conversation safety. Not HIPAA-compliant and not intended for PHI.
- Not designed for high-volume production without scaling

## License

All rights reserved.

This repository is published as a portfolio demonstration of my work in
AI-powered business automation for dental clinics.

The code is provided for review and evaluation purposes only.
No commercial use, redistribution, or modification is permitted without
explicit written permission from the author.

For commercial use, licensing discussions, or custom development based
on this architecture — please contact me directly.
