# Backlog

This file records ideas that arose after APPROVE of a completed phase.
No idea here is lost — it will be considered in future phases.

**Policy:** Once a phase receives APPROVE, all new ideas go here, not back into the current phase.

---

## Critical

*None yet.*

## High

*None yet.*

## Medium

*None yet.*

## Low

*None yet.*

## Technical Debt

*None yet.*

## Future Ideas

*None yet.*
## Phase 7D.2 Follow-up (из аудита)

### High Priority (критично для production)

#### Testing Debt
- [ ] Add explicit `assert result.is_fallback is True` in fallback tests
- [ ] Add unit test for `notify_staff_followup_complete()`

### Medium Priority

#### Code Quality
- [ ] **2.3**: Consolidate duplicate `_write_to_crm()` calls
- [ ] **2.4**: Add validation for `score_rules` keys in qualification.json

### Low Priority

#### Performance & Reliability
- [ ] **3.1**: Implement SQLite connection pooling
- [ ] **3.2**: Add cleanup for stale chat_ids in `_rate_limit` dict
- [ ] **3.3**: Improve `check_safety()` substring matching with word boundaries
- [ ] **3.4**: Add field validation in Lead model (phone, email format)

#### Code Consistency
- [ ] **4.1**: Convert dataclasses to Pydantic models
- [ ] **4.2**: Clarify `apply_transition()` return value
- [ ] **4.3**: Fix `LLMClient._fallback()` intent semantics
- [ ] **4.4**: Move `temperature=0.1` to AppConfig

