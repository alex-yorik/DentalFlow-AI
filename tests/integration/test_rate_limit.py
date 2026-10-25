import os
import urllib.error
import urllib.request

import pytest

BASE_URL = os.environ.get("NGINX_TEST_URL", "http://localhost:80")
BURST = 40
RATE = 10
BURST_LIMIT = 20


def _nginx_reachable() -> bool:
    try:
        with urllib.request.urlopen(f"{BASE_URL}/health", timeout=2):
            return True
    except Exception:
        return False


@pytest.mark.skipif(not _nginx_reachable(), reason="nginx not running")
def test_rate_limit_returns_429_on_burst():
    seen = []
    for _ in range(BURST):
        try:
            with urllib.request.urlopen(
                f"{BASE_URL}/api/chat", data=b"{}", timeout=2
            ) as resp:
                seen.append(resp.status)
        except urllib.error.HTTPError as e:
            seen.append(e.code)
    assert 429 in seen, f"expected 429, got {sorted(set(seen))}"


@pytest.mark.skipif(not _nginx_reachable(), reason="nginx not running")
def test_security_headers_present():
    with urllib.request.urlopen(f"{BASE_URL}/health", timeout=2) as resp:
        headers = resp.headers
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("X-Content-Type-Options") == "nosniff"


@pytest.mark.skipif(not _nginx_reachable(), reason="nginx not running")
def test_server_tokens_off():
    with urllib.request.urlopen(f"{BASE_URL}/health", timeout=2) as resp:
        server = resp.headers.get("Server", "")
        assert server == "nginx"
