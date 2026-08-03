# Backup & Restore Runbook

## Overview
SQLite бэкапится службой `backup` в docker-compose. Бэкап делается через
`sqlite3.Connection.backup()` (консистентный снапшот, безопасен при WAL),
а НЕ копированием живого `database.db`. Каждый бэкап проверяется
`PRAGMA integrity_check`. Хранятся последние 7 бэкапов.

- Бэкапы: `data/backups/database-YYYY-MM-DD.db`
- Период: `BACKUP_INTERVAL_HOURS` (по умолчанию 6 ч в compose, 24 ч в коде)
- Хранение: `BACKUP_RETENTION_DAYS` (по умолчанию 7)
- При сбое бэкапа шлётся Telegram-алерт (через `Alerter`, если задан `ALERTS_CHAT_ID`)

## Восстановление (restore)

1. **Остановите сервисы приложения**, чтобы БД не писалась:
   ```bash
   docker-compose stop telegram web followup watchdog backup
   ```
2. Проверьте целостность и восстановите из бэкапа:
   ```bash
   docker-compose run --rm backup python docker/restore_backup.py
   # или конкретный файл:
   docker-compose run --rm backup python docker/restore_backup.py data/backups/database-2026-08-03.db
   ```
   Скрипт сам проверяет `integrity_check` и откажется от битого бэкапа.
   После восстановления скрипт запускает миграции и приводит схему БД
   к актуальной версии (`alembic upgrade head`). Если миграция упала —
   скрипт завершится с ненулевым кодом.
3. **Приведите схему БД к актуальной версии** (если restore выполнялся
   вручную, минуя `restore_backup.py`, или миграция не применилась):
   ```bash
   docker-compose run --rm backup python -m alembic \
     -c src/storage/alembic.ini upgrade head
   ```
4. **Запустите сервисы обратно:**
   ```bash
   docker-compose up -d
   ```
5. Проверьте рабочий статус: `docker-compose ps` и `/health` веб-сервиса.

> Примечание: скрипт восстановления не трогает данные в памяти (`_response_store`)
> и не проверяет хэши; полную проверку данных сделайте на копии перед боевым
> восстановлением.
