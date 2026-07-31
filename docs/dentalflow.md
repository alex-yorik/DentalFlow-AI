# DentalFlow

## Lead State Machine

Leads progress through a finite state machine with explicit transitions:

```
new ──→ collecting ──→ qualifying ──→ qualified ──→ crm_written ──→ followup ──→ closed
```

| State | Description |
|-------|------------|
| `new` | Initial state when a user sends the first message |
| `collecting` | System is gathering lead fields (name, phone, service interest) |
| `qualifying` | All critical fields collected; qualification score computed |
| `qualified` | Score meets or exceeds `crm_write_threshold` (default: 25) |
| `crm_written` | Lead data sent to CRM provider |
| `followup` | Follow-up campaign is active for this lead |
| `closed` | Lead completed, converted, or expired |

All transitions go through `validate_transition()` before `apply_transition()`. The transition table in `src/leads/state_machine.py` defines every legal `(from, to)` pair with a reason.

## CRM Pipeline

```
Lead data collected
       │
       ▼
Qualification scoring
  - has_name         → +10
  - has_phone        → +10
  - has_email        → +5
  - has_service      → +10
  - has_preferred_time → +5
  - intent is new appointment → +10
  - urgency is urgent → +5
       │
       ▼
Score ≥ threshold (25)? ──yes──→ CRM write → state = crm_written
       │
       no
       ▼
Request missing fields → state = collecting
```

CRM access goes through `CRMProvider` interface (`src/integrations/crm/provider.py`). The active provider is selected by the `DENTALFLOW_CRM_PROVIDER` environment variable. Currently implemented: `mock` (stores in SQLite, logs to console).

## Follow-up Behaviour

The `FollowUpEngine` runs as an asyncio background task that polls the database every `poll_interval_seconds` (default: 30).

```
crm_written → followup (task created in DB)
       │
       ├── delay_minutes (60) → send initial template
       ├── max_retries ≥ 1    → send reminder template
       └── max_retries = 0    → send final template → closed
```

Three message templates are defined in `clients/<name>/followup.json`:
- **initial** — first contact: "Hi {name}, we noticed you were interested in {service_interest}..."
- **reminder** — second contact: "Just a friendly reminder..."
- **final** — last attempt: "This is our last follow-up..."

Optimistic locking (`UPDATE ... WHERE status='pending'`) prevents double execution in concurrent scenarios.

## FAQ and Safety Routing

### FAQ

When a user asks a common question, the system matches it against pattern lists in `clients/<name>/faq.json`:

| FAQ Patterns | Answer Source |
|-------------|--------------|
| hours, open, business hours | FAQ entry → hours |
| address, location, directions | FAQ entry → address |
| phone, contact number | FAQ entry → phone |
| insurance | FAQ entry → insurance |
| cost, prices, fees | FAQ entry → cost estimate |
| services, treatments | FAQ entry → service list |
| new patient, first visit | FAQ entry → new patient info |
| payment, financing | FAQ entry → payment options |

Matched FAQs are answered directly from config without calling the LLM.

### Safety

1. **Blocked phrases** — messages containing words from `rules.json/blocked_phrases` (price, cost, diagnosis, prescription, cure, etc.) are rejected with a configured error message.
2. **Refusal counter** — after `max_refusal_count` blocked attempts (default: 3), the bot stops engaging and directs the user to call the clinic.
3. **Out-of-scope** — if the LLM returns `action: out_of_scope`, the bot replies with a configured error message asking the user to stay within dental topics.
4. **LLM fallback** — if the OpenAI API fails or returns unparseable output, the system uses a safe default reply.