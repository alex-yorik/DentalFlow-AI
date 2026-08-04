# Deploy Checklist — DentalFlow AI (v0.10.3)

Чистый сервер: Ubuntu 24.04, Docker Compose. Gotchas → AGENTS.md «Проектные gotchas».

## 1. Пререквизиты
```bash
# Docker engine + compose plugin
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin git
sudo usermod -aG docker $USER && newgrp docker
docker --version && docker compose version && git --version
```

## 2. Клонирование
```bash
git clone <repo-url> && cd DentalFlow-AI
git checkout v0.10.3
```

## 3. Настройка .env
```bash
cp .env.example .env
nano .env   # или любой редактор
```
Заполнить: `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`,
`ALERTS_CHAT_ID`, `OPENAI_MODEL=openai/gpt-4o-mini`.
> `.env` в `.gitignore` — никогда не коммитить (security.md:81).

## 4. Права на data/
```bash
sudo chown -R 1000:1000 data/
```
> UID=1000 это `appuser` из Dockerfile. Иначе SQLite → "readonly database"
> (gotcha AGENTS.md:52-54).

## 5. Docker Compose валидация
```bash
docker-compose config                 # валидация схемы (gotcha №1, AGENTS.md:44-46)
docker-compose up -d --build          # сборка и запуск
```
> Compose-ошибки не ловятся pytest и code review — config обязателен.

## 6. Post-deploy проверки
```bash
docker-compose ps                     # 6 сервисов Up: telegram web followup nginx watchdog backup
curl -s http://localhost/health       # → 200
docker-compose logs -f --tail=30      # нет traceback; watchdog идёт на http://web:8080/health (AGENTS.md:111-113)
```
- **Bot test**: `/start` в Telegram → ответ ресепшена.
- **Backup**: `ls data/backups/` — файлы `database-YYYY-MM-DD.db` + ротация 7 дней (backup_runbook.md).
- **Alerts**: непустой `ALERTS_CHAT_ID` — при сбое приходит алерт (backup_runbook.md:12).

## 7. SSL (по docs/ssl_setup.md)
```bash
sudo apt-get install -y certbot
sudo certbot certonly --webroot -w /tmp/acme-challenge -d your-domain.com
sudo cp /etc/letsencrypt/live/your-domain.com/{fullchain,privkey}.pem docker/certs/
sudo chown -R 1000:1000 docker/certs/
docker-compose down && docker-compose up -d --build
docker-compose exec nginx nginx -t    # syntax is ok
```
- Проверка: `curl -k -I https://localhost` → 200 + заголовки X-Frame/X-Content.
- Renewal-cron: `0 3 * * * sudo certbot renew --quiet` (см. ssl_setup.md:57-63). Редирект 301 включать только после проверок DoD (rate limit 429 ломается).

## 8. Troubleshooting
- **"readonly database"** → `sudo chown -R 1000:1000 data/` (п.4).
- **Compose не стартует** → `docker-compose config` до `up`; сервисы ходят по имени `http://web:8080`, не по IP (AGENTS.md:49, 114).
- **Сервис Unhealthy/restarting при живых логах** → worker healthcheck требует `WATCHED_SERVICE`/`HEARTBEAT_INTERVAL`, заданы ТОЛЬКО в `environment:` блоке compose для telegram/followup (docker-compose.yml:15-16, 84-85), в .env их нет. Потеря блока при правке compose → healthcheck молча падает (exit 1). Проверка: `docker-compose config | grep -A3 WATCHED_SERVICE`.
- **HTTP 429** → rate-limit nginx (burst недетерминирован, AGENTS.md:109-117) — это ожидаемо после простоя.
- **Миграции/restore** → только `python -m alembic -c src/storage/alembic.ini upgrade head`; корневого alembic.ini НЕТ (AGENTS.md:47-48, backup_runbook.md:33).
