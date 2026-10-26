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

## T7. Честность README и документации

- Коммит: `3a7ff1c` — «T7: honest README (AI-assisted authorship, measured numbers), privacy section, docs disclaimers and index».
- Изменены: `README.md`, `docs/security.md` (дисклеймер), `docs/reports/final_auditor_report.md` (только шапка-дисклеймер), создан `docs/README.md` (индекс).

### T7.0. Измеренные числа (только они идут в README)

| Метрика | Команда | Значение |
|---|---|---|
| Тест-файлы | `find tests -name "test_*.py" \| wc -l` | 33 |
| Тест-функции | `grep -rhE "^\s*(async )?def test_" tests \| wc -l` | 291 |
| Покрытие (statement) | `pytest -q --cov=src --cov-report=term` | 78% (`298 passed, 3 skipped`) |

### T7.6. Контроль честности

`grep -rniE "entirely by the author|implemented by the author|zero downtime|production-ready|independent audit|passed a full" README.md docs`:

- `README.md` — «This is not an independent audit» → допустимый контекст.
- `docs/README.md` — «not an independent audit» → допустимый контекст.
- `docs/ROADMAP.md:79` — «production-ready» в формулировке цели этапа. Файл вне Allowed files T7, не правился. См. «Открытые вопросы».

## T8. Финальная проверка и отчёт

- Дата: 2026-10-26
- Ветка: `chore/portfolio-hardening`, head `3a7ff1c` (до коммита T8)

### T8.1. Чистый клон — VERIFIED

```
git clone -b chore/portfolio-hardening git@github.com:alex-yorik/DentalFlow-AI.git /tmp/df-t8
# head = 3a7ff1c
cp .env.example .env
# NGINX_PORT=8091, NGINX_SSL_PORT=8443; OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL
# скопированы из рабочего .env локально (не коммитились)
docker compose config -q            # OK
make certs                          # OK
docker compose up -d web nginx      # web + nginx up
sudo chown -R 1000:1000 data/
docker compose restart web          # шаг из README
curl -sk https://localhost:8443/health
# {"status":"ok","service":"dentalflow",...}  HTTP 200
curl -s -X POST http://localhost:8091/api/chat -H 'Content-Type: application/json' \
  -d '{"channel_id":"demo-patient-t8","text":"Hi! Do you accept new patients?"}'
# {"reply":"Yes, Bright Smile Dental accepts new patients! ..."}  HTTP 200 → VERIFIED
docker compose down && rm -rf /tmp/df-t8
```

Замечание: первый `curl` сразу после `restart web` вернул 502 (nginx стартовал раньше web). После готовности web `/health` = 200. Поведение воспроизводимо и не блокирует quick-start.

### T8.2. Полный набор в рабочем репо — VERIFIED

| Проверка | Команда | Результат |
|---|---|---|
| Компиляция | `python -m compileall -q src tests` | OK |
| Тесты + покрытие | `pytest -q --cov=src --cov-report=term \| tail -5` | 298 passed, 3 skipped; **78%** |
| Линт | `ruff check src tests` | All checks passed |
| Типы | `mypy src` | Success: no issues found in 57 files |
| Секьюрити | `bandit -r src -ll` | Medium 0, High 0 |
| Docker image | `docker build -t dentalflow-ai .` | OK, `sha256:ce4dd9f3…` |
| Compose | `docker compose config -q` | OK |
| Рабочее дерево | `git status --short` | пусто (чисто) |

### T8.3. CI (анонимный GitHub API)

- Команда: `curl -s "https://api.github.com/repos/alex-yorik/DentalFlow-AI/actions/runs?per_page=5&branch=chore/portfolio-hardening"`
- Head ветки `3a7ff1c` → `completed` / **`success`**
- URL: https://github.com/alex-yorik/DentalFlow-AI/actions/runs/40246056484

### Задачи T0–T8

| Задача | Статус | Коммит(ы) | Доказательство |
|---|---|---|---|
| T0 Baseline | DONE | `ba22657` | pytest 270 passed, отчёт T0 |
| T1 deps + docs refs | DONE | `640c790`, `0628e7a` | `pip install -r requirements-dev.txt`, pytest зелёный |
| T2 CI blocking + autofix | DONE | `951e209`, `208a345` | CI: ruff/mypy/bandit блокирующие; ruff 174→0 |
| T3 web/WhatsApp hardening | DONE | `2d61e93` | mock tests + test_web_security.py; CI success |
| T4 safe_phrases whitelist | DONE | `079b8e3` | test_safety/test_config зелёные |
| T5 fresh-clone quick-start | DONE | `079b40b`, `af797bd` | T8.1 — VERIFIED |
| T6 git history secret scan | DONE | `215430c` | gitleaks: 1 ожидаемая находка |
| T7 honest README | DONE | `3a7ff1c` | числа T7.0; контрольный grep — только допустимые контексты |
| T8 final verification | DONE | (этот коммит) | T8.1 VERIFIED, T8.2 VERIFIED, T8.3 `success` |

### Подавления (suppressions)

| Тип | Место | Причина |
|---|---|---|
| `# nosec B104` | `src/config/loader.py:123` | Bind `0.0.0.0` внутри контейнера — необходим для Docker-сети; наружу трафик идёт через nginx. |
| `# nosec B310` | `src/monitoring/watchdog.py:36` | URL берётся из доверенного конфига `WATCHDOG_WEB_URL` (внутренний сервис, http). |
| `# type: ignore` | — | Отсутствуют (проверено `grep -rn "type: ignore" src/ tests/`). |
| `# noqa: BLE001` | `src/entrypoints/backup.py:34`, `src/entrypoints/watchdog.py:45`, `src/monitoring/heartbeat.py:53`, `src/monitoring/alerter.py:35`, `src/monitoring/watchdog.py:41`, `src/monitoring/watchdog.py:53` | 6 мест — **pre-existing**, не добавлены в ходе hardening; широкий `except` в фоновых сервисах логируется/алертится. |

### Изменённые существующие тесты

| Задача | Файлы | Обоснование |
|---|---|---|
| T2 (`951e209`, `208a345`) | `test_conversation_flow.py`, `test_crm_failure.py`, `test_rate_limit.py`, `test_watchdog.py` | Lint-only: unused import, аннотации, приведения типов. Поведение не менялось. |
| T3 (`2d61e93`) | `test_web_adapter.py`, `test_whatsapp_adapter.py` | Удалён тест истории `/messages`, обновлён WhatsApp-стаб под ужесточённую проверку; добавлен `test_web_security.py`. |
| T4 (`079b8e3`) | `test_config.py`, `test_safety.py` | Только добавлены новые кейсы для safe_phrases (89 вставок); существующие ассерты не переписаны. |
| T5–T8 | — | Тесты не изменялись. |

### Отклонения от ТЗ (owner-approved)

1. **T1-followup** — правка `docs/process/FASTAPI_TESTING.md` (`requirements.txt` → `requirements-dev.txt`), вне Allowed files T1. Разрешено владельцем.
2. **T5 A1** — `.env.example`: `ALERTS_CHAT_ID=0` с комментарием (иначе `cp .env.example .env` ломает `load_config()`). Разрешено владельцем.
3. **T7.0** — таблица чисел перенесена из `docs/reports/hardening-report.md` (вне Allowed files T7) в отчёт T8. Разрешено владельцем.

### Открытые вопросы

1. **`docs/ROADMAP.md:79`** — «production-ready» в формулировке цели этапа. Файл вне Allowed files T7/T8. Не критично: это цель (Docker/CI/monitoring уже реализованы), а не заявление о готовности.
2. **`release.yml`** — NOT VERIFIED: workflow релиза не имеет `permissions: actions: write`, логов успешного прогона нет (тег не пушился в рамках hardening). Не входит в DoD этой ветки; проверить при первом релизе.

### Baseline → итог

| Метрика | Baseline (T0) | Итог (T8) |
|---|---|---|
| pytest passed | 270 | 298 |
| ruff | 174 | 0 |
| mypy | 21 | 0 |
| bandit Medium | 2 | 0 |
| Тест-файлы | 32 | 33 |
| Тест-функции | 273 | 291 |
| Покрытие | — | 78% |

### Definition of Done (9 пунктов)

1. **Тесты зелёные** — `pytest -q` → 298 passed, 3 skipped. ✅
2. **Линт чистый** — `ruff check src tests` → All checks passed. ✅
3. **Типы чистые** — `mypy src` → no issues in 57 files. ✅
4. **Security scan без Medium/High** — `bandit -r src -ll` → 0. ✅
5. **Docker image собирается** — `docker build -t dentalflow-ai .` → OK. ✅
6. **Compose-конфиг валиден** — `docker compose config -q` → OK. ✅
7. **Quick-start из чистого клона** — T8.1 → health 200, chat VERIFIED. ✅
8. **Документация честная** — T7 контрольный grep → только «not an independent audit». ✅
9. **CI ветки зелёный** — run 40246056484 → success. ✅

### Статус PR

PR #1 **НЕ смержен**. Ветка запушена, head проверен, требуется приёмка владельца.
