# DentalFlow AI

AI-ресепшн и система автоматизации лидов для клиник. Telegram-бот общается с пациентами как виртуальный администратор, отвечает на вопросы по услугам и расписанию, собирает контактные данные, квалифицирует лида по скорингу и передаёт его в CRM. Бизнес-логика полностью вынесена в конфигурацию клиента (JSON), поэтому бота можно перенастроить на другую клинику без изменения кода.

Демо-конфигурация — клиника **Bright Smile Dental** (демо-клиент `demo_dental`).

## Функциональность
- **AI-ресепшн** — отвечает на вопросы о часах работы, адресе, услугах и FAQ на основе конфигурации клиента
- **Квалификация лидов** — собирает имя, телефон, интерес к услуге; скоринг (правила + баллы) определяет готовность лида к записи
- **State machine лидов** — явный конечный автомат жизненного цикла лида от `new` до `closed`
- **CRM-интеграция** — интерфейс провайдера, в комплекте mock-провайдер (готов к HubSpot/Salesforce)
- **Follow-up движок** — фоновые напоминания с настраиваемыми задержками и повторами
- **Безопасность диалога** — блокировка запрещённых тем (цены, диагнозы, рецепты), лимит отказов, безопасный дефолтный ответ
- **Веб-канал** — тот же обработчик сообщений доступен через FastAPI (Telegram — первый канал, архитектура поддерживает web/WhatsApp)
- **Мониторинг и бэкапы** — watchdog, heartbeat, алерты в Telegram, резервное копирование БД

## Стек технологий
- Python 3.12, async/await
- python-telegram-bot 20.x (Telegram-канал)
- FastAPI + Uvicorn (веб-канал), Nginx (прокси + rate-limit)
- OpenAI API (structured output с Pydantic)
- SQLite (aiosqlite, WAL) + Alembic (миграции)
- Pydantic v2 (валидация конфига)
- Docker + docker-compose
- pytest / pytest-asyncio (тесты), ruff / mypy (линт и типы)

## Архитектура

Проект разделён на изолированные подсистемы (`src/`), каждый процесс — отдельный entrypoint в docker-compose:

```
Telegram-канал (bot.py) ─┐
Веб-канал (FastAPI) ─────┼─▶ message_processor ─▶ rules/safety → LLM (OpenAI)
                         │          │
                         ▼          ▼
                  lead state machine   conversation store (SQLite)
                         │
                         ▼
                    CRM provider (интерфейс)
```

Сервисы (docker-compose):
- **telegram** — python-telegram-bot, приём и обработка сообщений
- **web** — FastAPI `/api/chat`, `/health`, `/metrics` (за nginx)
- **followup** — фоновые напоминания и повторные касания
- **watchdog** — проверка здоровья сервисов, алерты в Telegram
- **backup** — резервное копирование SQLite через sqlite3 backup API
- **nginx** — TLS, заголовки безопасности, rate-limit

Данные: SQLite в `data/` (volume), схема — Alembic-миграции (`src/storage/alembic`). Конфигурация клиента — JSON в `clients/<client>/` (business, services, faq, rules, qualification, followup, prompts). `src/main.py` — только dev-точка входа, продакшен запускается через отдельные entrypoints.

## Безопасность
Проект прошёл полный аудит безопасности (2026-08-07). Реализовано:
- Fail-closed аутентификация конфигурации — обязательные переменные (`TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`) проверяются при старте, дефолтов нет
- Rate-limit на nginx: 10 req/min на `/api/chat` (burst=20), 30 req/min на `/health` и `/metrics` (ответ 429)
- Заголовки безопасности: `X-Frame-Options: DENY`, `nosniff`, `CSP default-src 'self'`, `server_tokens off`
- Безопасность диалога: блокировка запрещённых фраз, лимит отказов, безопасные сообщения по умолчанию
- WAL + `busy_timeout=5000` (блокировки БД устранены)
- Бэкапы по расписанию (по умолчанию каждые 6 ч) с ротацией (по умолчанию 7 дней)
- .dockerignore + .gitignore — `.env`, `data/`, тесты и docs вне Docker-образа и git
- Multi-container деплой (build → up -d) без даунтайма

Все секреты (`TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`) хранятся в `.env`, не в коде.

## Установка
1. Скопируй `.env.example` в `.env`
2. Заполни `TELEGRAM_BOT_TOKEN` и `OPENAI_API_KEY` (остальные параметры уже имеют дефолты)
3. `docker-compose up -d`

## Деплой
```bash
docker-compose build && docker-compose up -d
docker-compose logs -f --tail=30
```

После первого деплоя: `chown -R <uid контейнера> data/` (иначе SQLite откроется как read-only).
