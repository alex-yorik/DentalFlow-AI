# Phase 7D.2 — Error Handling Hardening

**Goal:** Make all database, API, and startup errors fail gracefully with structured logging instead of crashing or silently corrupting state.

---

## Subphase 7D.2.1 — Repository + Storage Safety

**Goal:** Wrap all SQLite operations in `repository.py` with typed exception handling so that transient DB failures (locked, timeout, constraint) never propagate as unhandled crashes. Add a `StorageError` exception type and return `None` / raise controlled errors instead of bare `Exception`.

### Tasks

1. **Add `StorageError` exception in `src/storage/database.py`**
   - Files: `src/storage/database.py`
   - Add `class StorageError(Exception): pass`
   - Wrap `get_connection()` in try/except → raise `StorageError`

2. **Wrap all DB operations in `src/leads/repository.py`**
   - Files: `src/leads/repository.py`
   - Every public function: catch `StorageError` + `aiosqlite.Error`, log with context (chat_id, lead_id, operation name), re-raise or return safe default
   - `create_lead` → raise `StorageError` on INSERT failure
   - `get_lead_by_chat_id` → return `None` on failure
   - `update_lead` → raise `StorageError` on UPDATE failure
   - `lead_exists` → return `False` on failure
   - `delete_lead` → raise `StorageError` on DELETE failure

3. **Wrap DB operations in `src/followup/__init__.py`**
   - Files: `src/followup/__init__.py`
   - Same pattern: catch `StorageError` + `aiosqlite.Error` in all 6 internal functions
   - Log with context (task_id, lead_id), return safe defaults

### Definition of Done
- [ ] `StorageError` exists in `src/storage/database.py`
- [ ] All 5 repository functions catch DB errors
- [ ] All 6 followup internal functions catch DB errors
- [ ] Errors logged with context (chat_id, operation, error type)
- [ ] `python3 -m py_compile` passes on changed files
- [ ] All existing 142 tests pass

---

## Subphase 7D.2.2 — Handler + CRM Error Recovery

**Goal:** Prevent leads from getting stuck in `CRM_WRITE` state when CRM calls fail. Add structured error handling to `handle_message()` and `_write_to_crm()`.

### Tasks

1. **Fix `_write_to_crm` in `src/channels/telegram/handlers.py`**
   - On CRM failure: don't silently swallow — transition lead back to `QUALIFYING` or `CLOSED` with `escalation_needed=True`
   - Log CRM errors with lead context

2. **Wrap entire `handle_message` in `src/channels/telegram/handlers.py`**
   - Add top-level try/except in `handle_message()`
   - On unexpected error: log with full context (chat_id, user_text), send `error_generic` message to user
   - Do not crash the polling loop

3. **Add CRM retry logic in `src/integrations/crm/mock.py`** (optional, as mock is simple)
   - No changes needed to mock — prepare interface for real provider retry

### Definition of Done
- [ ] CRM write failure transitions lead out of `CRM_WRITE`
- [ ] `handle_message` has top-level try/except
- [ ] Errors logged with chat_id + user_text context
- [ ] `python3 -m py_compile` passes on changed files
- [ ] All existing tests pass

---

## Subphase 7D.2.3 — Startup + Graceful Shutdown

**Goal:** Make `main.py` robust against startup failures (DB, config, Telegram API). Ensure partial failures don't leave dangling resources.

### Tasks

1. **Wrap startup sequence in `src/main.py`**
   - `init_db()` → catch, log, exit cleanly
   - `create_bot()` → catch invalid token, log, exit cleanly
   - `followup_engine.start()` → catch, log, continue without followup

2. **Ensure shutdown cleans up partial state**
   - If followup_engine failed to start, don't call `stop()` on it
   - Use `try/finally` for shutdown sequence

### Definition of Done
- [ ] DB init failure logs and exits cleanly
- [ ] Invalid token logs and exits cleanly
- [ ] Followup engine failure doesn't block bot
- [ ] Shutdown handles partial initialization
- [ ] All existing tests pass