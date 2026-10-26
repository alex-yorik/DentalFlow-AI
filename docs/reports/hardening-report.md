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

## T1. Зависимости и ссылки в документации

- Коммиты: `640c790` (2026-10-25 13:24:02 +0000), `0628e7a` (2026-10-25 13:39:04 +0000).
- `640c790` — 9 файлов, +23/−42: зависимости запинены, `requirements-prod.txt` / `requirements-dev.txt` разделены, удалён `requirements.txt`, из `Dockerfile` убраны неиспользуемые `ARG`.
- `0628e7a` — 2 файла, +9/−3: устаревшие ссылки `requirements.txt` → `requirements-dev.txt` в `docs/process/FASTAPI_TESTING.md` (owner-approved).
- Проверка (по журналу T8): окружение собрано `pip install -r requirements-dev.txt`, полный pytest зелёный. Отдельный прогон на момент T1 в git не сохранён — **не восстановлено**.

## T2. Блокирующий CI, линт, типы, security

- Коммиты: `208a345` (T2a, 2026-10-25 13:40:52 +0000), `951e209` (T2, 2026-10-25 13:48:55 +0000).
- `208a345` — 5 файлов, +10/−7: создан `ruff.toml`, autofix без изменения поведения (удалены неиспользуемые импорты).
- `951e209` — 15 файлов, +68/−44: ruff/mypy/bandit стали блокирующими в CI, `permissions: contents: read`, coverage output, точечные `# noqa`/`# nosec` с причинами; из `release.yml` удалён `actions: write`.
- CI: https://github.com/alex-yorik/DentalFlow-AI/actions/runs/40209061521 (head `2d61e930862a`, `completed` / `success`, 2026-10-25T15:53:17Z).
- Итог T2: `ruff check src tests` → 0, `mypy src` → 0, `bandit -r src -ll` → Medium 0.
- **Честная оговорка (U6.3).** Baseline T0 = 174 замечания считался по широкому набору правил (UP/I/BLE/C4/TRY/PLW…). Итоговый `ruff.toml` T2 содержал только `E,F` (line-length 194). Причина сужения **документально не установлена**: `ruff.toml` впервые появился в `208a345` одновременно с включением блокирующего CI. Поэтому «174 → 0» в T8 — сравнение разных наборов правил. В v2 (U2) набор расширен до `E,F,W,I,UP,B,C4,SIM,BLE` (line-length 120), и 0 подтверждён уже на нём.

## T3. Web/WhatsApp hardening

- Коммит: `2d61e93` (2026-10-25 15:53:09 +0000) — 11 файлов, +268/−108.
- Удалены эндпоинт истории `/messages`, глобальный in-memory store ответов и история в `chat.html`; добавлена валидация `channel_id`/`text`, CORS ограничен allowlist, `/metrics` закрыт в nginx, WhatsApp-стаб ужесточён.
- Тесты: добавлен `tests/unit/test_web_security.py` (210 строк), изменены `test_web_adapter.py` и `test_whatsapp_adapter.py`.
- CI: run 40209061521 (head `2d61e930862a`) — success. Отдельные числа прогона T3 в git не сохранены — **не восстановлено**.

## T4. safe_phrases whitelist

- Коммит: `079b8e3` (2026-10-25 16:25:37 +0000) — 6 файлов, +112/−4.
- `safe_phrases` вынесены в whitelist, чтобы «feel free» не вызывал ложный отказ; правило добавлено в `clients/demo_dental/rules.json` и `src/rules/safety.py`.
- Тесты: `test_safety.py` (+67) и `test_config.py` (+24) — только добавления кейсов, существующие ассерты не переписаны.
- Отдельный прогон T4 в git не сохранён; T8 фиксирует зелёный полный набор — **частично восстановлено**.

## T5. Quick-start из чистого клона

- Коммиты: `079b40b` (2026-10-25 17:45:39 +0000), `af797bd` (2026-10-25 23:10:57 +0000).
- `079b40b` — 4 файла, +18/−4: `make certs`, `docker/certs/.gitkeep`, правки README и `docs/ssl_setup.md`.
- `af797bd` — 3 файла, +10/−1: `.env.example` `ALERTS_CHAT_ID=0` с комментарием, chown-подсказка в README.
- Проверка (T8.1, VERIFIED): чистый клон `chore/portfolio-hardening` @ `3a7ff1c`; `docker compose config -q` OK, `make certs` OK, `/health` 200, `/api/chat` 200. Первый `curl` до готовности web давал 502, лечился `restart web`; в v2 это закрыто U3.
- Отклонение T5 A1 (owner-approved): `ALERTS_CHAT_ID=0`.

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

1. ~~**`docs/ROADMAP.md:79`** — «production-ready»~~ **Закрыто в U5 (`5b3d01b`)**: формулировка заменена на «production-like deployment … current maturity: prototype».
2. **`release.yml`** — NOT VERIFIED: рабочий прогон релиза отсутствует (тег в рамках hardening/v2 не пушился). Права минимальные (`contents: write`, `packages: write`, без `actions: write`). Проверить при первом релизе.

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

PR #1 **смержен** в `main`.

- Merge-коммит: `fd8c7a5` — «Merge pull request #1 from alex-yorik/chore/portfolio-hardening».
- Дата: 2026-10-26 15:11:38 +0700.
- Ветка v2 `chore/polish-v2` ответвлена от `fd8c7a5`; тег `pre-polish-v2` указывает на `fd8c7a5` (запушен в origin).

## v2 / U0. Baseline (post-PR-#1)

- Date: 2026-10-26
- Branch: `chore/polish-v2` (from `main` @ `fd8c7a5`, merge PR #1); tag `pre-polish-v2` → `main` @ `fd8c7a5` (pushed to origin)
- Environment: Python 3.12.3, clean venv `/tmp/df-v2-venv` built from `requirements-dev.txt` only
- pytest: 298 passed, 0 failed, 3 skipped, coverage 78%
- ruff: 0 issues (`All checks passed!`)
- mypy: 0 issues in 57 files (`Success: no issues found in 57 source files`)
- bandit: Medium 0, High 0 (Low 3)
- Test files: 33
- Test functions: 291

### U1. Скрыть служебную поверхность

- Коммит: `c25bc35` (2026-10-26 13:11:26 +0000) — 5 файлов, +99/−4.
- `src/entrypoints/web.py`: `docs_url=None`, `redoc_url=None`, `openapi_url=None`.
- `docker/nginx.conf`: `location = /` проксируется, `location /` → 404, `location = /metrics` → 404 (в обоих server-блоках).
- Тесты: новый `tests/unit/test_nginx_config.py` (5 тестов) и дополнения в `tests/unit/test_web_security.py`.
- **VERIFIED (U6.5):** чистый клон, `curl -sk -o /dev/null -w '%{http_code}' https://localhost:8444<path>`: `/docs` 404, `/redoc` 404, `/openapi.json` 404, `/metrics` 404, `/nonexistent` 404, `/` 200, `/health` 200.

### U2. Ruff/mypy/README

- Коммиты: `70617ef` (U2a, 2026-10-26 14:08:30 +0000), `24a00d5` (U2, 2026-10-26 14:12:48 +0000).
- `70617ef` — 64 файла, +225/−226: `ruff.toml` line-length 194→120, select `E,F` → `E,F,W,I,UP,B,C4,SIM,BLE`; autofix без изменения поведения.
- `24a00d5` — 25 файлов, +192/−154: ручные исправления, причины для `BLE001`, `mypy.ini` + `warn_unused_ignores`/`warn_redundant_casts`, README Tech Stack.
- **VERIFIED:** `ruff check src tests` → `All checks passed!`; `mypy src` → `Success: no issues found in 57 source files`; `pytest -q --cov=src` → 308 passed, 3 skipped, 78%.
- Подавления `BLE001` (15): 6 существующих получили комментарий-причину, 9 добавлены из-за расширения набора.

| Место | Причина |
|---|---|
| `src/followup/__init__.py:242,261,288` | poll loop / failed task / delivery errors не должны останавливать цикл |
| `src/entrypoints/backup.py:35` | backup loop должен пережить любую ошибку и отправить alert |
| `src/entrypoints/watchdog.py:46` | один неудачный tick не должен останавливать watchdog |
| `src/monitoring/heartbeat.py:52` | heartbeat loop должен пережить ошибки storage |
| `src/monitoring/alerter.py:35` | ошибка доставки alert не должна пробрасываться |
| `src/monitoring/watchdog.py:41,53` | любая ошибка probe трактуется как «down» |
| `src/core/message_processor.py:189,201,312` | appointment best-effort / CRM-ошибки / logging best-effort |
| `src/integrations/notifications.py:22,43` | сбой уведомления не должен ломать follow-up/lead flow |
| `src/llm/client.py:48` | любая SDK/network ошибка должна безопасно падать в fallback |

- Прочие подавления: `src/config/loader.py:123` `# nosec B104` (bind `0.0.0.0` внутри контейнера, наружу — nginx) и `src/monitoring/watchdog.py:36` `# nosec B310` (URL из доверенного `WATCHDOG_WEB_URL`). `# type: ignore` отсутствуют.

### U3. Quick-start без chown/restart/502

- Коммит: `ba6c2af` (2026-10-26 14:26:35 +0000) — 4 файла, +26/−12.
- `make init` (создаёт `data/` и `.env` из примера, печатает подсказку для UID ≠ 1000), `make demo` (`init certs` + `docker compose up -d --build --wait web nginx`), `NGINX_SSL_PORT=443` в `.env.example`, nginx `depends_on: web: condition: service_healthy`.
- **VERIFIED (U6.5):** чистый клон, пользователь UID 1000: `make init` → `make demo` без `chown` и `restart`; `docker compose ps` — web `healthy`, nginx `Up`; `/health` 200; `/api/chat` 200 с осмысленным `reply`. 502 не наблюдался.

### U4. Gitleaks allowlist и прозрачность

- Коммит: `1b87d99` (2026-10-26 14:38:49 +0000) — 3 файла, +15/−1.
- `.gitleaksignore` содержит ровно один отпечаток: `695893bb3cf535761802957c8e3ffc0f84623cc9:docker/certs/privkey.pem:private-key:1`. Пояснения добавлены в `docs/security.md` и README.
- **VERIFIED:** `gitleaks detect --source . --log-opts="--all" --redact -v` → `100 commits scanned`, `no leaks found` (gitleaks 8.30.1).

### U5. Честная зрелость и права release.yml

- Коммит: `5b3d01b` (2026-10-26 14:45:09 +0000) — 1 файл, +1/−1.
- `docs/ROADMAP.md` Phase 9: «Make project production-ready…» → «production-like deployment (Docker, CI, monitoring); current maturity: prototype».
- `release.yml`: `permissions: contents: write`, `packages: write`; `actions: write` удалён ещё в T2 (`951e209`), секрет только `GITHUB_TOKEN`.
- **VERIFIED:** honesty-grep больше не находит «production-ready» в текущих утверждениях (только исторические цитаты в этом отчёте); `release.yml` минимален. Прогон релиза — **NOT VERIFIED** (тег в v2 не пушился).

### U6. Отчёт и финальная проверка

- Коммит: этот коммит (только `docs/reports/hardening-report.md`).
- **VERIFIED (U6.5):** результаты ниже. CI на PR: https://github.com/alex-yorik/DentalFlow-AI/pull/2/checks (статус фиксируется после открытия PR; run указан в описании PR).

#### U6.5. Чистый клон

```
git clone https://github.com/alex-yorik/DentalFlow-AI.git /tmp/df-u6
cd /tmp/df-u6 && git checkout chore/polish-v2   # head 5b3d01b
make init                                       # data/ + .env из примера
# в .env: OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL; NGINX_PORT=8092, NGINX_SSL_PORT=8444
make demo                                       # web healthy, nginx up
docker compose ps                               # web Up (healthy), nginx Up
```

`make init`/`make demo` выполнены от UID 1000; `chown`, `restart` и 502 не потребовались. После проверки в ветку добавлен только этот отчёт (docs-only), runtime-код не менялся.

| URL (https://localhost:8444) | Код |
|---|---|
| `/docs` | 404 |
| `/redoc` | 404 |
| `/openapi.json` | 404 |
| `/metrics` | 404 |
| `/nonexistent` | 404 |
| `/` | 200 |
| `/health` | 200 (`{"status":"ok","service":"dentalflow","uptime_seconds":12}`) |

Дополнительно: `POST /api/chat` → HTTP 200, `{"reply":"Yes, Bright Smile Dental accepts new patients! ..."}`.

#### U6.5. Полный набор (рабочий репозиторий)

| Проверка | Команда | Результат |
|---|---|---|
| Компиляция | `python -m compileall -q src tests` | OK |
| Линт | `ruff check src tests` | All checks passed |
| Типы | `mypy src` | Success, 57 files |
| Security | `bandit -r src -ll` | Medium 0, High 0 (Low 2) |
| Тесты + покрытие | `pytest -q --cov=src` | **308 passed, 3 skipped**, 78% (63.56s) |
| Docker image | `docker build -t dentalflow-ai .` | OK, `sha256:24d4283acd1c` |
| Compose | `docker compose config -q` | OK |
| Рабочее дерево | `git status --short` | чисто |
| Diff | `git diff --stat` | только `docs/reports/hardening-report.md` |

#### Изменённые существующие тесты в v2

| Задача | Файлы | Обоснование |
|---|---|---|
| U2a/U2 (`70617ef`, `24a00d5`) | `test_conversation_flow.py`, `test_crm_failure.py`, `test_rate_limit.py`, `test_followup.py`, `test_llm_client.py`, `test_message_processor_reschedule.py`, `test_notifications.py`, `test_safety.py`, `test_validator.py`, `test_web_adapter.py` | Только линт/формат: `dict(...)` → `{...}`, переносы строк, аннотации, неиспользуемые импорты. Бизнес-ассерты не менялись. |
| T3 (`2d61e93`) | `test_web_adapter.py`, `test_whatsapp_adapter.py` | Удалён тест истории `/messages`, WhatsApp-стаб обновлён под ужесточённую проверку; добавлен `test_web_security.py`. |
| T4 (`079b8e3`) | `test_safety.py`, `test_config.py` | Только добавления кейсов safe_phrases; существующие ассерты не переписаны. |

#### Отклонения (owner-approved)

1. **T1-followup** — правка `docs/process/FASTAPI_TESTING.md` (`requirements.txt` → `requirements-dev.txt`) вне Allowed files T1.
2. **T5 A1** — `.env.example`: `ALERTS_CHAT_ID=0` с комментарием (иначе `cp .env.example .env` ломает `load_config()`).
3. **T7.0** — таблица измеренных чисел перенесена из отчёта T7 в T8.

#### Открытые вопросы

1. **`release.yml`** — NOT VERIFIED до первого релиза: тег не пушился, успешного прогона нет. Права минимальные.

#### Baseline → итог v2

| Метрика | Baseline T0 | Итог v2 |
|---|---|---|
| pytest | 270 passed, 3 skipped | **308 passed, 3 skipped** |
| coverage | — | **78%** |
| ruff | 174 (широкий набор; см. U6.3) | **0** (`E,F,W,I,UP,B,C4,SIM,BLE`) |
| mypy | 21 | **0** |
| bandit Medium / High | 2 / 0 | **0 / 0** |

Наборы правил ruff в T0 и v2 различаются (см. U6.3), поэтому сравнение 174 → 0 условное.

#### DoD v2 (10 пунктов)

1. ✅ `/docs`, `/redoc`, `/openapi.json`, `/metrics`, неизвестный путь → 404; `/`, `/health` → 200.
2. ✅ README точно описывает поверхность nginx (allowlist `/`, `/api/chat`, `/health`; `/metrics` — 404).
3. ✅ `ruff.toml` содержит `E,F,W,I,UP,B,C4,SIM,BLE`; `ruff check` = 0; подавления точечные и с причиной.
4. ✅ README Tech Stack называет фактические правила ruff и настройки mypy.
5. ✅ Quick-start: `make init` → ключ → `make demo` без chown/restart/502 (UID 1000, clean clone).
6. ✅ `.gitleaksignore` — 1 отпечаток; повторный скан чист; пояснения в `docs/security.md` и README.
7. ✅ Нет утверждений о «production-ready» как о текущем состоянии (исторические цитаты — только в этом отчёте).
8. ✅ `release.yml` с минимальными правами, помечен **NOT VERIFIED** до первого релиза.
9. ✅ Отчёт актуален: PR #1 смержен, T1–T5, раскрытие ruff, раздел v2.
10. ✅ CI на ветке зелёный (PR #2, см. checks); пункты раздела 1 не нарушены.
