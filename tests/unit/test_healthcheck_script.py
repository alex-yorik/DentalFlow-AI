import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent.parent
HEALTHCHECK_SCRIPT = HERE / "docker" / "healthcheck.py"

HEALTH_OK_SERVER = """
import json, os
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, *a): pass

port = int(os.environ.get("TEST_PORT", "18080"))
HTTPServer(("", port), H).serve_forever()
"""

HEALTH_FAIL_SERVER = """
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(500)
        self.end_headers()
    def log_message(self, *a): pass

port = int(os.environ.get("TEST_PORT", "18080"))
HTTPServer(("", port), H).serve_forever()
"""


HEALTH_OK_CUSTOM_SERVER = """
import json, os
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, *a): pass

port = int(os.environ.get("TEST_PORT", "18080"))
HTTPServer(("", port), H).serve_forever()
"""


@pytest.fixture
def health_server_port(unused_tcp_port_factory):
    return unused_tcp_port_factory()


def _run_server(code, port):
    env = {**__import__("os").environ, "TEST_PORT": str(port)}
    proc = subprocess.Popen(
        [sys.executable, "-c", code],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    import time

    time.sleep(0.3)
    return proc


@pytest.fixture
def health_ok_server(health_server_port):
    proc = _run_server(HEALTH_OK_SERVER, health_server_port)
    yield health_server_port
    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture
def health_fail_server(health_server_port):
    proc = _run_server(HEALTH_FAIL_SERVER, health_server_port)
    yield health_server_port
    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture
def health_ok_custom_server(health_server_port):
    proc = _run_server(HEALTH_OK_CUSTOM_SERVER, health_server_port)
    yield health_server_port
    proc.terminate()
    proc.wait(timeout=5)


class TestHealthcheckScript:
    def test_exit_0_when_health_returns_200(self, health_ok_server):
        port = health_ok_server
        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            env={"WEB_HOST": "localhost", "WEB_PORT": str(port)},
            capture_output=True,
        )
        assert result.returncode == 0

    def test_exit_0_with_custom_health_path(self, health_ok_custom_server):
        port = health_ok_custom_server
        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            env={"WEB_HOST": "localhost", "WEB_PORT": str(port), "HEALTH_PATH": "/healthz"},
            capture_output=True,
        )
        assert result.returncode == 0

    def test_exit_1_when_custom_path_not_matched(self, health_ok_server):
        port = health_ok_server
        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            env={"WEB_HOST": "localhost", "WEB_PORT": str(port), "HEALTH_PATH": "/healthz"},
            capture_output=True,
        )
        assert result.returncode == 1

    def test_exit_1_when_connection_refused(self):
        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            env={"WEB_HOST": "localhost", "WEB_PORT": "19999"},
            capture_output=True,
        )
        assert result.returncode == 1

    def test_exit_1_when_status_not_200(self, health_fail_server):
        port = health_fail_server
        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            env={"WEB_HOST": "localhost", "WEB_PORT": str(port)},
            capture_output=True,
        )
        assert result.returncode == 1

    def test_uses_default_host_and_port_when_no_env(self):
        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
        )
        assert result.returncode == 1

    def test_py_compile(self):
        result = subprocess.run(
            [sys.executable, "-c", f"import py_compile; py_compile.compile(r'{HEALTHCHECK_SCRIPT}', doraise=True)"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0