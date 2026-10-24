import logging

from src.core.logging import setup_logging, uvicorn_log_config


def test_setup_logging_silences_http_client_loggers():
    setup_logging("DEBUG", "json")

    try:
        assert logging.getLogger("httpx").level == logging.WARNING
        assert logging.getLogger("httpcore").level == logging.WARNING
    finally:
        setup_logging("INFO", "json")


def test_uvicorn_log_config_pins_http_client_loggers_to_warning():
    config = uvicorn_log_config("info", "json")

    for name in ("httpx", "httpcore"):
        assert config["loggers"][name]["level"] == "WARNING"
        assert config["loggers"][name]["propagate"] is False
