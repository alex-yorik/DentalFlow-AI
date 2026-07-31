# Security

## Threat Model

DentalFlow AI is an AI receptionist for a dental clinic. The following threats are considered in-scope:

| Threat | Risk | Mitigation |
|--------|------|------------|
| LLM gives **medical advice** (diagnosis, prescription) | High | Blocked phrases + UNSAFE intent → BLOCKED state |
| LLM quotes **prices, discounts, guarantees** | High | Blocked phrases in reply and extracted fields |
| **Prompt injection** — user tricks LLM into ignoring system prompt | Medium | Structured Outputs, Pydantic validation, low temperature |
| **SQL injection** via message text | Low | Parameterized queries only (`?` placeholders) |
| **PII leakage** via conversation storage | Medium | Structured summaries (500 char max), no raw transcripts |
| **Unauthorized CRM writes** | High | LLM has no CRM access — Python enforces `CRMProvider` interface |

The model of trust is: **LLM is untrusted**. Every proposed action is validated by Python before execution.

---

## AI Safety Layer — `check_safety()`

File: `src/rules/safety.py`

The function `check_safety(output, rules)` runs three checks in sequence:

1. **Blocked phrases in `reply_text`** — if the AI's reply contains a word from `rules.blocked_phrases`, the output is rejected with `escalate=True`.
2. **Blocked phrases in `extracted_fields`** — same check applied to every extracted field (name, phone, service, etc.).
3. **UNSAFE intent with `safe=False`** — if the AI classifies the intent as `UNSAFE` and the safety flag is `False`, the output is rejected.

`escalate=True` causes the lead to enter `LeadState.BLOCKED`. Once blocked, all messages get a fixed `error_unsafe` response and no further AI calls are made.

Blocked phrases (from `clients/<name>/rules.json`):

```
price, cost, cheap, discount, free, guarantee,
diagnosis, prescription, painkiller, antibiotic,
cure, heal, natural remedy
```

These prevent the AI from discussing pricing, guarantees, or medical treatment.

`max_refusal_count` is defined in `RulesConfig` (default: 3) but the refusal counter is **not yet implemented** in the safety check. This is a known gap.

---

## Output Validation — `validate_ai_output()`

File: `src/rules/validator.py`

Even if the safety check passes, every AI output is validated for logical consistency:

1. **Confidence threshold** — `confidence < rules.confidence_threshold` (default 0.5) → reject.
2. **Lead + wrong action** — if `is_lead=True` but action is `CLOSE` or `ANSWER_FAQ` → reject (illogical).
3. **Non-lead + wrong action** — if `is_lead=False` but action is `QUALIFY` or `CRM_WRITE` → reject.
4. **UNSAFE + `safe=True`** — inconsistent combination → reject.

---

## Prompt Injection Mitigation

The system uses a layered defence — no single mechanism is relied upon:

1. **Structured Outputs** — OpenAI `parse()` API guarantees the response conforms to the `AIOutput` Pydantic schema. The model cannot change the output format or embed arbitrary instructions.
2. **Pydantic validation** — every field is type-checked (`confidence: float 0..1`, `intent: Intent enum`, etc.). Malformed JSON triggers a safe fallback.
3. **Low temperature** — `temperature=0.1` reduces output variability and the likelihood of following injected instructions.
4. **System prompt** — located in `clients/<name>/prompts/system.md`, defines the AI's role as a dental receptionist.
5. **Fallback** — any OpenAI API exception returns `intent="off_topic"`, `confidence=0.0`, `escalation_needed=True`.

**Known gap**: user input is passed directly to the LLM without sanitization or rate limiting. Protection relies on the output-side checks described above.

---

## Secret Management

| Secret | Source | Storage |
|--------|--------|---------|
| `TELEGRAM_BOT_TOKEN` | `.env` | `AppConfig.telegram_bot_token` (Pydantic), never logged |
| `OPENAI_API_KEY` | `.env` | `AppConfig.openai_api_key`, passed to `LLMClient(api_key=...)` |
| `OPENAI_MODEL` | `.env` | Model name string, default `gpt-4o-mini` |

- `.env` is in `.gitignore` — never committed.
- `.env.example` provides a safe template.
- In Docker, `.env` is injected via `env_file:` in `docker-compose.yml`.
- Tests use `"test_key"` / `"test_token"` — no real credentials.
- Missing `TELEGRAM_BOT_TOKEN` prevents the bot from starting.

---

## SQL Injection Prevention

All database queries use **parameterized statements** via `aiosqlite`:

```python
await conn.execute(
    "SELECT * FROM leads WHERE telegram_chat_id = ?",
    (telegram_chat_id,)
)
```

No raw string interpolation is used anywhere in the codebase.

---

## CRM Isolation

The LLM **never writes** to the CRM directly. The AI returns a `suggested_action` (e.g., `crm_write`), and Python code decides whether to execute it. All CRM access goes through the `CRMProvider` interface:

```
LLM → AIOutput.suggested_action → Python validate → CRMProvider.write_lead()
```

The default provider is `MockCRMProvider` — in-memory only, no external system touched.

---

## State Machine Safety

The lead state machine (`src/leads/state_machine.py`) enforces:

- All transitions must be declared in the `_TRANSITION_TABLE`.
- `BLOCKED` is a **terminal state** — no transition out of it is allowed.
- `CLOSED` can only transition to `BLOCKED`.
- Transition to `CRM_WRITE` requires a qualification score above the configured threshold.
- Transition to `QUALIFYING` requires all `critical_fields` to be collected.

---

## Known Gaps

| Gap | Impact | Priority |
|-----|--------|----------|
| No rate limiting on user messages | A single user can flood the AI, incurring OpenAI costs | Medium |
| No input sanitization before LLM call | User can attempt prompt injection via message text | Medium |
| `max_refusal_count` not enforced in code | Safety config declares 3 refusals, but no counter tracks them | Low |
| No coverage of security paths in tests | Safety and validation logic lacks dedicated security test scenarios | Low |