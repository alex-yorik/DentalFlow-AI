import re
from pathlib import Path

NGINX_CONFIG = Path(__file__).resolve().parents[2] / "docker" / "nginx.conf"


def _read_config() -> str:
    return NGINX_CONFIG.read_text(encoding="utf-8")


def _server_blocks(text: str) -> list[str]:
    return re.findall(r"server\s*\{\n(.*?)\n\}", text, re.DOTALL)


def test_two_server_blocks_present():
    assert len(_server_blocks(_read_config())) == 2


def test_server_tokens_disabled():
    assert "server_tokens off;" in _read_config()


def test_each_server_returns_404_for_metrics():
    blocks = _server_blocks(_read_config())
    assert blocks
    for block in blocks:
        assert re.search(
            r"location\s*=\s*/metrics\s*\{\s*return\s+404\s*;", block
        ), "location = /metrics must return 404"


def test_each_server_has_final_location_returning_404():
    blocks = _server_blocks(_read_config())
    assert blocks
    for block in blocks:
        assert re.search(
            r"location\s*/\s*\{\s*return\s+404\s*;", block
        ), "location / must return 404"


def test_no_metrics_proxy_pass():
    text = _read_config()
    assert "location /metrics" not in text
    assert not re.search(r"location\s*=\s*/metrics\s*\{[^}]*proxy_pass", text)
