# Testing

## Overview

DentalFlow AI uses **pytest** (>=8.0) with **pytest-asyncio** (>=0.23) for async test execution.

Configuration (`pytest.ini`):

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

`asyncio_mode = auto` wraps every async test in a dedicated event loop automatically — no decorator needed.

---

## Test Categories

| Category | Count | Path | Isolation |
|----------|-------|------|-----------|
| **Unit** | 9 files | `tests/unit/` | Fully isolated — DB mocked via `monkeypatch`, OpenAI mocked via `AsyncMock` |
| **Integration** | 1 file | `tests/integration/` | Full cycle through `handle_message()` with mock LLM and temp SQLite |

---

## How to Run

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Single test file
pytest tests/unit/test_safety.py -v

# Single test case
pytest tests/unit/test_safety.py::TestSafetyCheck::test_price_in_reply_blocked

# Inside Docker
docker-compose run --rm bot pytest
```

---

## Test Files Reference

### Unit Tests

| File | Module Tested | Key Scenarios |
|------|---------------|---------------|
| `test_safety.py` | `rules/safety.py` | Blocked phrases in reply/text/fields, UNSAFE intent, escalate flag |
| `test_validator.py` | `rules/validator.py` | Confidence below threshold, inconsistent lead/action combinations, UNSAFE+safe clash |
| `test_config_loader.py` | `config/loader.py` | Client config loading, env var overrides, Pydantic validation |
| `test_state_machine.py` | `leads/state_machine.py` | All valid transitions, all invalid transitions, BLOCKED immutability |
| `test_lead_repository.py` | `leads/repository.py` | CRUD operations: create, get, update, delete, exists |
| `test_llm_contracts.py` | `llm/contracts.py` | Pydantic model validation, JSON deserialization, boundary values |
| `test_llm_client.py` | `llm/client.py` | `analyze()` with mock OpenAI, API failure → safe fallback |
| `test_qualification.py` | `rules/qualification.py` | Score calculation, threshold logic, edge cases |
| `test_followup.py` | `followup/__init__.py` | Task acquire/complete/error, graceful shutdown, dual-acquire prevention |

### Integration Tests

| File | Scope |
|------|-------|
| `test_conversation_flow.py` | Full dialog cycle: `/start` → FAQ → lead qualification → safety block → CRM write → followup scheduling |

---

## Fixtures & Mocks

### Common Fixtures (`tests/conftest.py`)

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `demo_client_config` | function | Loads `demo_dental` client config from JSON files |
| `demo_app_config` | function | Builds `AppConfig` with test tokens |
| `db_path` | function | Creates temp SQLite file, applies SCHEMA, yields path, cleans up |
| `db` | function | Monkeypatches `storage.database.get_connection` to return temp DB |

### Mocking Patterns

- **AsyncMock** — for `OpenAI client.beta.chat.completions.parse`
- **MagicMock** — for Telegram `Update` and `Context.DEFAULT_TYPE`
- **monkeypatch** — for DB connection replacement (`monkeypatch.setattr`)
- **unittest.mock.patch** — for `FollowUpEngine._run_loop` in followup tests

---

## Test Database Strategy

- Each test that needs DB access creates an isolated **temporary SQLite file** via `tempfile.NamedTemporaryFile`
- SCHEMA is applied at fixture setup (`CREATE TABLE IF NOT EXISTS`)
- WAL mode and foreign keys are enabled
- File is deleted at fixture teardown — no cross-test state contamination

---

## Coverage

`pytest-cov` is **not** currently configured. Adding it is a recommended future improvement:

```bash
pip install pytest-cov
pytest --cov=src tests/
```

A `.coveragerc` file should be added to exclude test files and third-party code from reporting.