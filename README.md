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

- **Patient:** Hi! Do you accept new patients?
- **Bright Smile Dental:** Yes, Bright Smile Dental accepts new patients! If you're interested in scheduling an appointment, I can help you with that.
- **Patient:** I would like to book a teeth cleaning.
- **Bright Smile Dental:** Great! I can help you with that. Could you please provide your name and phone number so we can check availability and confirm your appointment?
- **Patient:** Patient, +7 999 ***-**-11.
- **Bright Smile Dental:** Thank you, Patient! I have your name and phone number. Now, could you please let me know your preferred date and time for the teeth cleaning appointment?
- **Patient:** Saturday morning works for me.
- **Bright Smile Dental:** I understand that Saturday morning works for you. However, please note that we are closed on Saturdays. Could you provide an alternative date or time for your teeth cleaning appointment?
- **Patient:** Then Monday at 10am.
- **Bright Smile Dental:** Thank you, Patient! I have noted your preferred time for a teeth cleaning appointment on Monday at 10 AM. We will check availability and confirm with you shortly.

## Tech Stack
- Python 3.12, async/await
- python-telegram-bot 20.x (Telegram channel)
- FastAPI + Uvicorn (web channel), Nginx (proxy + rate limiting)
- OpenAI API (structured output with Pydantic)
- SQLite (aiosqlite, WAL) + Alembic (migrations)
- Pydantic v2 (config validation)
- Docker + docker-compose
- pytest / pytest-asyncio (tests), ruff (rule families: E, F, W, I, UP, B, C4, SIM, BLE), mypy (default strictness plus warn_unused_ignores, warn_redundant_casts), bandit (medium+ severity)

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
- **web** — FastAPI /api/chat, /health, /metrics, and the demo chat page / (nginx exposes only /, /api/chat and /health; everything else returns 404; /metrics is internal-network only)
- **followup** — background reminders and follow-up touches
- **watchdog** — service health checks, Telegram alerts
- **backup** — SQLite backups via the sqlite3 backup API
- **nginx** — TLS, security headers, rate limiting

Data: SQLite in `data/` (volume), schema managed by Alembic migrations (`src/storage/alembic`). Client configuration is JSON in `clients/<client>/` (business, services, faq, rules, qualification, followup, prompts). `src/main.py` is a dev-only entrypoint; production runs through dedicated entrypoints.

## Multi-Channel Support

Telegram: the most tested channel (prototype stage). Web: demo channel.
WhatsApp: adapter stub, not wired into the app.
Architecture supports adding: Slack (Bot API), SMS via Twilio, Facebook Messenger (Meta Business API), Microsoft Teams (Bot Framework).

Channels are isolated entrypoints sharing the same message processor. They use the common `IncomingMessage` contract and `OutgoingAdapter` protocol (`src/channels/base.py`); there is no plugin registry — adding a channel means adding an entrypoint plus an adapter.

## Security
Security measures below were reviewed in an AI-assisted self-review
(see docs/security.md). This is not an independent audit.
- Fail-fast configuration validation: required variables are checked at startup, no defaults for secrets.
- Nginx rate limiting: 10 req/min on `/api/chat` (burst=20), 30 req/min on `/health` (HTTP 429)
- `/metrics` is not exposed through nginx (returns 404); it is reachable only inside the Docker network
- API documentation endpoints (/docs, /redoc, /openapi.json) are disabled
- nginx uses an allowlist of routes; any other path returns 404
- Security headers: `X-Frame-Options: DENY`, `nosniff`, `CSP default-src 'self'`, `server_tokens off`
- Conversation safety: blocked phrases, refusal limit, safe messages by default
- WAL + `busy_timeout=5000` (database locking eliminated)
- Scheduled backups (every 6 h by default) with rotation (7 days by default)
- `.env` and `data/` are git-ignored; `.env`, `data/`, tests and docs are excluded from the Docker image (`.dockerignore`).
- Multi-container deployment (build → up -d)
- Full git history was scanned with gitleaks (8.30.1, 2026-10-26): the only finding is a throwaway self-signed localhost key committed early and since removed (see `docs/security.md`).

All secrets (`TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`) are stored in `.env`, never in code.

## Installation
1. `make init` — create `data/` and copy `.env.example` to `.env` if needed.
2. Edit `.env`: set `OPENAI_API_KEY`. For OpenRouter or another OpenAI-compatible endpoint, also set `OPENAI_BASE_URL` and `OPENAI_MODEL`. `TELEGRAM_BOT_TOKEN` is needed only for the Telegram service.
3. `make demo` — build and start `web` + `nginx`, wait until `web` is healthy, and generate local TLS certificates.

`make certs` creates a self-signed certificate for local demonstration only. For a public server, use trusted Let's Encrypt certificates instead — see [docs/ssl_setup.md](docs/ssl_setup.md).

Containers run as UID 1000. `make init` creates `data/` as your current user; if your UID is not 1000, it prints a hint. To fix permissions, run `sudo chown -R 1000:1000 data/` (not needed when your user is UID 1000).

## Try It Without Telegram

The web channel runs on the same message processor as the bot, so the full flow works without a Telegram token:

```bash
make init
# edit .env: set OPENAI_API_KEY (and OPENAI_BASE_URL/OPENAI_MODEL for OpenRouter)
make demo
curl -sk https://localhost:443/health
curl -sk -X POST https://localhost:443/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"channel_id":"demo-patient-1","text":"Hi! Do you accept new patients?"}'
```

If you changed `NGINX_SSL_PORT` in `.env`, use that port in the URL instead of `443`.

`make certs` generates a self-signed certificate for local demonstration. A public server needs a trusted Let's Encrypt certificate — see [docs/ssl_setup.md](docs/ssl_setup.md).

`POST /api/chat` takes `channel_id` (1-64 chars, letters/digits/`_`/`-`) and `text` (1-2000 chars), and returns `{"reply": "..."}`. Use a new `channel_id` for a fresh conversation; replies are returned per request and are not stored in memory. Cross-origin browser access is disabled by default; set `CORS_ALLOW_ORIGINS` (comma-separated) to allow specific origins.

Only `OPENAI_API_KEY` is required for the web demo — `TELEGRAM_BOT_TOKEN` is needed only by the `telegram` service. If port 80 is busy, set `NGINX_PORT` in `.env` and use that port in the URL.

## Deployment
A public server must use trusted Let's Encrypt certificates; `make certs` is for local demonstration only. See [docs/ssl_setup.md](docs/ssl_setup.md).

```bash
docker-compose build && docker-compose up -d
docker-compose logs -f --tail=30
```

After the first deployment: `chown -R <container uid> data/` (otherwise SQLite will open as read-only).

## Tests

The project includes 33 test files with 291 test functions (unit + integration); measured statement coverage is 78% (`pytest --cov=src`):

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Authorship & How This Was Built

I am not a professional software developer. This project was built with AI
coding assistants ("vibe coding"). My role: I define the product idea,
requirements and acceptance criteria, direct the AI tools through a documented
multi-role workflow (see `docs/process/` and `docs/PROJECT_STATE.md`), run the
results, review behavior, and decide what ships. Most of the code was generated
by AI models; I did not write it line by line by hand.

What this means for you as a reader:
- I can explain the product, the architecture and the behavior at a high level,
  but this repository is **not** evidence of classic programming experience.
- Reviews and "audits" in this repo (`docs/security.md`, `docs/reports/`) are
  AI-assisted self-reviews, **not** independent third-party audits.
- What this repository does show: my ability to specify software, orchestrate AI
  tools, set up tests/CI/deployment, and iterate to a working prototype.

## Data & Privacy

The bot collects the patient's name and phone number during lead qualification.
Message texts are sent to an external LLM service (OpenAI) for processing. For
real-world use you need the patient's consent, a data-retention policy, and a
review of local personal-data legislation. This project does not claim
compliance with any privacy or medical-data regulation.

## What I Would Do Next

1. Real CRM integration (replace the mock provider with a client's actual CRM).
2. Web-channel authentication for production.
3. Load testing.
4. Independent code review.
5. WhatsApp webhook signature verification.

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
