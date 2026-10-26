# FastAPI Testing Guidelines

## ⚠️ Критически важное правило

**НЕ используйте `app.routes` для проверки маршрутов!**

### Почему?

В разных версиях FastAPI разное поведение:

- **FastAPI < 0.129**: `app.routes` содержит маршруты напрямую
- **FastAPI >= 0.130**: `app.routes` оборачивает роутеры в `_IncludedRouter`

Это ломает тесты при обновлении FastAPI!

---

## ✅ Правильный способ проверки маршрутов

### Вместо:
```python
# ❌ НЕПРАВИЛЬНО — сломается на FastAPI >= 0.130
paths = {route.path for route in app.routes}
assert "/api/chat" in paths
```

### Используйте:
```python
# ✅ ПРАВИЛЬНО — работает на всех версиях
assert "/api/chat" in app.openapi()["paths"]
```

**Или:**
```python
# ✅ Тоже работает
from fastapi.routing import APIRoute
paths = {route.path for route in app.routes 
         if isinstance(route, APIRoute)}
```

---

## 🔧 Фиксация версий

### В `requirements-dev.txt`:

```txt
# FastAPI — фиксируем мажорную версию
fastapi>=0.128.0,<0.130.0

# Или если нужна последняя:
fastapi>=0.141.0,<0.150.0
```

### В `requirements-dev.txt`:

```txt
# Для тестов используйте ту же версию что и в production
-r requirements-dev.txt
```

---

## 🧪 Шаблоны тестов

### Тест что маршрут существует:

```python
def test_api_chat_route_exists(self, demo_app_config):
    app = web._build_web_app(demo_app_config)
    
    # Правильный способ
    assert "/api/chat" in app.openapi()["paths"]
```

### Тест что маршрут работает:

```python
def test_api_chat_responds(self, demo_app_config):
    from fastapi.testclient import TestClient
    
    app = web._build_web_app(demo_app_config)
    client = TestClient(app)
    
    resp = client.post("/api/chat", json={"text": "hello"})
    assert resp.status_code == 200
```

---

## 🚨 Чеклист перед коммитом

- [ ] Тесты используют `app.openapi()["paths"]` а не `app.routes`
- [ ] Версии FastAPI зафиксированы в `requirements-dev.txt`
- [ ] CI использует ту же версию что и локальная разработка
- [ ] Нет прямого доступа к внутренним атрибутам FastAPI

---

## 📚 Полезные ссылки

- [FastAPI OpenAPI Schema](https://fastapi.tiangolo.com/reference/openapi/)
- [FastAPI Breaking Changes](https://github.com/tiangolo/fastapi/releases)

---

## 💡 Lesson Learned

**Август 2026**: 
- CI упал из-за обновления FastAPI 0.128.8 → 0.141.1
- Тест проверял `route.path` но в новой версии роутеры оборачиваются
- Решение: использовать `app.openapi()["paths"]` — стабильный API

**Вывод**: Никогда не тестируйте внутренние детали реализации!
Используйте публичный API (OpenAPI schema, TestClient).
