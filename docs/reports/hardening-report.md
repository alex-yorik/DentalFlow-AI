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
