from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.entrypoints.web import _build_web_app
from src.monitoring.metrics import metrics


def _app(monkeypatch, demo_app_config):
    monkeypatch.setattr("src.entrypoints.web.LLMClient", MagicMock)
    return _build_web_app(demo_app_config)


def test_health_reports_ok(monkeypatch, demo_app_config):
    client = TestClient(_app(monkeypatch, demo_app_config))
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "uptime_seconds" in body


def test_metrics_endpoint(monkeypatch, demo_app_config):
    metrics._counters.clear()
    metrics.inc("messages_processed", 3)
    client = TestClient(_app(monkeypatch, demo_app_config))
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.json()
    assert body["counters"]["messages_processed"] == 3
    assert body["uptime_seconds"] >= 0
