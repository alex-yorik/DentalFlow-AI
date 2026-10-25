# Hardening Report
## Журнал ИИ-assisted инженерных правок. Это не независимый аудит.

## T0. Baseline

- Дата: 2026-10-25
- Ветка: `chore/portfolio-hardening` (от `main` @ `1167f96`)
- Тег: `pre-portfolio-hardening` → `main` @ `1167f96` (запушены в origin)
- Окружение: Python 3.12.3, чистый venv `/tmp/df-venv`; `requirements.txt`, `requirements-dev.txt`, `ruff`, `mypy`

### Результаты

| Проверка | Результат |
|---|---|
| pytest | 270 passed, 0 failed, 3 skipped (27.96s) |
| ruff check src tests | 174 замечания (132 fixable) |
| mypy src | 21 ошибка в 7 файлах (57 файлов проверено) |
| bandit -r src -ll | Medium 2 (B104 `loader.py:121`, B310 `watchdog.py:35`); в summary также Low 1 — B110 (`handlers.py:143`), скрыт фильтром `-ll` |
| Файлов в git | 146 |
| Тест-файлов | 32 |
| Тест-функций | 273 |

### Детализация ruff (174)

| Правило | Кол-во | Правило | Кол-во |
|---|---|---|---|
| UP017 | 51 | F401 | 7 |
| I001 | 33 | UP035 | 5 |
| UP045 | 17 | UP041 | 3 |
| UP007 | 12 | G201 | 3 |
| BLE001 | 11 | UP032 | 2 |
| C408 | 9 | F841 | 2 |
| TRY203 | 8 | SIM102 / S110 / RET501 / PLR1711 | по 1 |
| PLW1510 | 7 |  |  |

Baseline-тесты зелёные: 0 failed. Можно переходить к T1.

## T1-followup (owner-approved)

- Отклонение от Allowed files T1: обновлены строки 45, 59, 94 в `docs/process/FASTAPI_TESTING.md` (`requirements.txt` → `requirements-dev.txt`). Разрешено владельцем.
- `docs/reports/hardening-report.md:9` не изменялся — исторический baseline T0.


## T2-followup (Step 0b of T4, owner-approved)

Пункт «GitHub CI — NOT VERIFIED» закрыт после перевода репозитория в публичный (анонимный GitHub API).

- Прогон: https://github.com/alex-yorik/DentalFlow-AI/actions/runs/40209061521
- Ветка: `chore/portfolio-hardening`, head SHA `2d61e930862a`
- Статус: `completed` / `success`
- Дата: 2026-10-25T15:53:17Z

## T5-followup (owner-approved, Step A)

- Отклонение от Allowed files T5: изменён `.env.example` — `ALERTS_CHAT_ID=0` с комментарием. Без этого `cp .env.example .env` даёт `int('')` в `load_config()` и web не стартует. Разрешено владельцем.
- README Installation / Try It: добавлен шаг `sudo chown -R 1000:1000 data/` после первого запуска (контейнеры работают под UID 1000, иначе SQLite открывается read-only).

## T6. Проверка истории git на секреты

- Дата: 2026-10-25
- Инструмент: `gitleaks 8.30.1`
- Источник: `git clone --mirror https://github.com/alex-yorik/DentalFlow-AI.git /tmp/df-mirror`
- Команда: `gitleaks detect --source . --log-opts="--all" --redact -v`
- Просканировано: 90 коммитов, ~508 KB, 1.06 s
- Результат: **1 находка** (только ожидаемая).

### Находки

| Правило | Файл | Коммит | Диспозиция |
|---|---|---|---|
| `private-key` | `docker/certs/privkey.pem` | `695893b` (2026-08-04) | Известная ожидаемая находка. Self-signed localhost-сертификат для локальной разработки, боевой ценности нет, регенерируется `make certs`. Удалён из трекинга в `d50277f`. Историю не переписывали (решение владельца). |

Других находок (Telegram/OpenAI/OpenRouter токены, пароли, ключи) нет. `trufflehog` не использовался — gitleaks доступен и дал результат.

### T6.3. История по чувствительным путям

`git log --all --full-history --oneline -- .env '*.pem' '*.db' '*.sqlite3'`:

- `d50277f` — удаление сертификатов из трекинга.
- `695893b` — добавление `docker/certs/fullchain.pem` и `docker/certs/privkey.pem`.

`.env`, `*.db`, `*.sqlite3` никогда не были в трекинге. В истории присутствуют только два файла: `docker/certs/fullchain.pem`, `docker/certs/privkey.pem`.

### T6.4. Персональные данные

Реальных телефонов/имён пациентов в истории и текущем дереве не найдено. Встречаются только синтетические тестовые значения:

- `+79160000000`–`+79160000003`, `+79161112233`, `+79990000011` — тестовые номера в `tests/`.
- `+1 (512) 555-0142` — вымышленный телефон клиники в `clients/demo_dental/business.json`.
- Демо-диалог в README остаётся маскированным: `+7 999 ***-**-11`, имя `Patient`.

Текущее дерево `HEAD` (ветка `chore/portfolio-hardening`) не содержит телефонов вне `tests/`.
