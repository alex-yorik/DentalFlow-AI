from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import pytest

from src.config.loader import AppConfig, MonitoringConfig, load_client_config
from src.monitoring.watchdog import SERVICES, Watchdog, _probe_web

T0 = datetime(2026, 8, 3, 12, 0, 0, tzinfo=timezone.utc)

_CLIENT = load_client_config("demo_dental")


def _cfg(heartbeat=30, cooldown=15) -> AppConfig:
    return AppConfig(
        telegram_bot_token="t",
        openai_api_key="k",
        client_name="demo_dental",
        client=_CLIENT,
        monitoring=MonitoringConfig(
            heartbeat_interval=heartbeat, alert_cooldown_minutes=cooldown
        ),
    )


def make_probe(state: dict):
    async def probe(service, now):
        return state.get(service, True)

    return probe


async def test_healthy_services_no_events():
    w = Watchdog(_cfg(), probe=make_probe({}), now_provider=lambda: T0)
    assert await w.tick() == []
    assert w.status == {s: "up" for s in SERVICES}


async def test_up_to_down_emits_down_once():
    state = {}
    probe = make_probe(state)
    w = Watchdog(_cfg(cooldown=15), probe=probe, now_provider=lambda: T0)
    assert await w.tick() == []

    state["web"] = False
    events = await w.tick()
    assert len(events) == 1 and events[0].kind == "down" and events[0].service == "web"

    events2 = await w.tick()
    assert events2 == []


async def test_down_cooldown_suppresses_then_re_emits():
    state = {}
    clock = {"t": T0}
    w = Watchdog(_cfg(cooldown=15), probe=make_probe(state), now_provider=lambda: clock["t"])
    assert await w.tick() == []

    state["web"] = False
    assert [e.kind for e in await w.tick()] == ["down"]

    state["web"] = True
    assert [e.kind for e in await w.tick()] == ["recovered"]

    state["web"] = False
    events = await w.tick()
    assert events == []

    clock["t"] = T0 + timedelta(minutes=16)
    state["web"] = True
    await w.tick()
    state["web"] = False
    events = await w.tick()
    assert [e.kind for e in events] == ["down"]


async def test_down_to_up_emits_recovered():
    state = {}
    probe = make_probe(state)
    w = Watchdog(_cfg(), probe=probe, now_provider=lambda: T0)
    assert await w.tick() == []

    state["web"] = False
    assert await w.tick()
    state["web"] = True
    events = await w.tick()
    assert len(events) == 1 and events[0].kind == "recovered" and events[0].service == "web"
    assert w.status["web"] == "up"


async def test_worker_stale_marked_down():
    state = {}
    probe = make_probe(state)
    w = Watchdog(_cfg(), probe=probe, now_provider=lambda: T0)
    assert await w.tick() == []

    state["telegram"] = False
    events = await w.tick()
    downs = [e.service for e in events if e.kind == "down"]
    assert downs == ["telegram"]


async def test_unhealthy_at_startup_no_spurious_down():
    state = {"web": False}
    w = Watchdog(_cfg(), probe=make_probe(state), now_provider=lambda: T0)
    assert await w.tick() == []
    assert w.status["web"] == "down"


def _start_server(status: int):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(status)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server


@pytest.mark.asyncio
async def test_probe_web_ok():
    server = _start_server(200)
    try:
        url = f"http://127.0.0.1:{server.server_port}/health"
        assert await _probe_web(url) is True
    finally:
        server.shutdown()


@pytest.mark.asyncio
async def test_probe_web_fails_on_error_status():
    server = _start_server(500)
    try:
        url = f"http://127.0.0.1:{server.server_port}/health"
        assert await _probe_web(url) is False
    finally:
        server.shutdown()


@pytest.mark.asyncio
async def test_probe_web_fails_on_unreachable():
    assert await _probe_web("http://127.0.0.1:1/health", timeout=0.5) is False
