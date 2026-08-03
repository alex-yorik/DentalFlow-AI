import asyncio

import inspect
import pytest
from fastapi.testclient import TestClient

from src.entrypoints import web
from src.entrypoints import followup as followup_entry


class TestWebEntrypoint:
    def test_health_endpoint(self, demo_app_config):
        app = web._build_web_app(demo_app_config)
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok" and body["service"] == "dentalflow"

    def test_build_app_includes_web_router(self, demo_app_config):
        app = web._build_web_app(demo_app_config)
        assert "/api/chat" in app.openapi()["paths"]

    def test_run_web_is_callable(self):
        assert callable(web.run_web)


class TestFollowupEntrypoint:
    def test_run_followup_is_async_function(self):
        assert asyncio.iscoroutinefunction(followup_entry.run_followup)

    def test_module_imports(self):
        assert inspect.ismodule(followup_entry)
