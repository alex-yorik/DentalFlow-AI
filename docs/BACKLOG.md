# Backlog & Known Limitations

**Last updated:** August 2026  
**Version:** v0.9.10 (Phase 9 Complete)  
**Audit:** Phase 9 Round 2 (independent review)

---

##  Known Limitations (не блокируют релиз v0.9.10)

### 3.1 `_response_store` — утечка памяти + не переживает рестарт/масштабирование

**Файлы:** `src/channels/web/adapter.py`, `src/channels/whatsapp/adapter.py`

**Проблема:**
- `_response_store: dict[str, list[dict]] = {}` — обычный процесс-локальный словарь в памяти
- Растёт бесконечно (записи по каждому `channel_id`/`phone_number` не удаляются никогда)
- Полностью пропадает при рестарте контейнера
- Если появится больше одного инстанса `web`-сервиса за балансировщиком — история ответов конкретного пользователя окажется видна только тому инстансу, который её сохранил

**Практическое влияние:**
- Для MVP/демо — приемлемо
- При долгой работе без рестарта — рост памяти (не критично, т.к. очищается при пустых deque)
- После рестарта пользователь потеряет историю ответов (но не состояние лида — оно в БД)

**Плановое решение (Phase 11+):**
- Redis или другая внешняя cache-система
- TTL для записей (автоочистка старых >24 часов)
- Или периодическая очистка старых записей

**Статус:** Принято как осознанный компромисс для MVP

---

### 2.3 Дублирование boilerplate между тремя каналами

**Файлы:** 
- `src/channels/telegram/handlers.py::handle_message`
- `src/channels/web/adapter.py::chat`
- `src/channels/whatsapp/adapter.py::whatsapp_webhook`

**Проблема:**
Во всех трёх адаптерах почти дословно повторяется:
1. Проверка `BLOCKED` → проверка `CLOSED` (обнулить лида)
2. `create_lead` если лида нет
3. Сборка `IncomingMessage`
4. Вызов `process_message`

Плюс почти идентичные `_response_store` и `OutgoingAdapter` классы.

**Практическое влияние:**
- Технический долг (изменения нужно вносить в 3 места)
- Риск рассинхронизации логики

**Плановое решение (Phase 10 или 11):**
- Вынести общую логику ("получить-или-создать лида с учётом BLOCKED/CLOSED") в `src/core/lead_lookup.py`:
```python
  async def resolve_lead(
      channel_id: str, 
      channel_type: str,
      repository: LeadRepository
  ) -> Lead | None:
      # lookup → BLOCKED → CLOSED→None → create
```
- Все 3 адаптера используют `resolve_lead()` вместо дублирования

**Статус:** В планах, не блокирует релиз

---

## ⚠️ Архитектурные замечания (на будущее)

### 4.1 `_SingletonConnection.close()` — намеренный no-op

**Файл:** `src/storage/database.py`

**Проблема:**
- Метод `close()` ничего не делает (чтобы код репозиториев, привычно вызывающий `conn.close()`, не убивал синглтон)
- Работает, но хрупко: любой новый код, который явно рассчитывает на настоящее закрытие соединения (например, в тестах с явным teardown), тихо этого не получит

**Рекомендация:**
- Явно задокументировать это поведение в докстроке модуля на уровне `get_connection()` (сейчас комментарий есть только в самом классе)

**Статус:** Работает, но требует документации

---

### 4.2 Data classes без pydantic

**Файлы:** 
- `src/rules/models.py` (`TransitionResult`, `SafetyVerdict`)
- `src/leads/state_machine.py` (`ValidationResult`, `QualificationResult`)

**Проблема:**
- По-прежнему обычные классы вместо pydantic
- Тогда как всё остальое (`Lead`, `AIOutput`, `IncomingMessage` как dataclass) — типизировано

**Практическое влияние:**
- Стилистическая непоследовательность
- Нет автоматической валидации

**Рекомендация:**
- Привести к pydantic в рамках общего рефакторинга

**Статус:** Косметическое, не критично

---

### 4.3 `temperature=0.1` захардкожен в LLM client

**Файл:** `src/llm/client.py`

**Проблема:**
- `temperature` захардкожена, не вынесена в конфиг

**Рекомендация:**
- Добавить в `LLMConfig` как настраиваемый параметр

**Статус:** Низкий приоритет

---

## 🔧 Что исправлено из прошлого аудита (Phase 9 Round 1)

| Было | Стало |
|------|-------|
| Zombie-состояние лида при частичном сбое CRM-записи | ✅ Исправлено (откат + явное `crm_contact_id = None`) |
| Мёртвый код при сбросе follow-up | ✅ Прямой `UPDATE` |
| Тихий отказ перехода состояния | ✅ Явный `logger.warning` |
| `confidence == 0.0` как маркер фолбэка | ✅ Явный `is_fallback: bool` |
| Substring-мэтчинг блокирующих фраз | ✅ Regex с `\b` границами слов |
| `score_rules: dict[str, Any]` без валидации | ✅ Типизированная `ScoreRules(BaseModel)` |
| Новое SQLite-соединение на запрос | ✅ Singleton-соединение на процесс |
| Неограниченный рост `_rate_limit` | ✅ Очистка пустых deque |
| Дублирующийся `_write_to_crm` | ✅ Убран |
| Схема БД руками | ✅ Alembic-миграции |

---

##  Приоритеты

### До Phase 10 (перед production):
- [x] 3.1 `_response_store` — задокументировать (сделано ✅)
- [ ] 4.1 `_SingletonConnection` — добавить docstring

### Phase 10 (Production Deployment):
- [ ] Мониторинг и алерты
- [ ] Backup БД
- [ ] SSL/TLS

### Phase 11 (Refactoring):
- [ ] 2.3 Вынести общую логику в `lead_lookup.py`
- [ ] 4.2 Привести data classes к pydantic
- [ ] 4.3 Вынести `temperature` в конфиг

### Backlog (низкий приоритет):
- [ ] Рассмотреть Postgres вместо SQLite (если потребуется масштабирование)
- [ ] Вынести Alembic-миграции в отдельный сервис (если станут проблемой)
- [ ] **Phase 11 Full JSON-Driven Core** (On hold: waiting for 2nd client outside appointment-based services) — см. `docs/adr/002-json-driven-core-scope.md`

---

**Last reviewed:** August 2026, Phase 9 Round 2 Audit
