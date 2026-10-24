import json
import logging
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        fields = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
        }
        if record.exc_info and record.exc_info[0]:
            fields["exc"] = self.formatException(record.exc_info)
        return json.dumps(fields, ensure_ascii=False)


def _silence_http_clients() -> None:
    for name in ("httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)


def setup_logging(log_level: str = "INFO", json_format: str = "json") -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)
    _silence_http_clients()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if json_format == "text":
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    else:
        formatter = JSONFormatter()

    handler.setFormatter(formatter)

    root.handlers.clear()
    root.addHandler(handler)


def uvicorn_log_config(log_level: str = "INFO", json_format: str = "json") -> dict:
    if json_format == "text":
        formatter_cls = "logging.Formatter"
        formatter_cfg = {"fmt": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}
    else:
        formatter_cls = "src.core.logging.JSONFormatter"
        formatter_cfg = {}

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": formatter_cls,
                **formatter_cfg,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["console"], "level": log_level, "propagate": False},
            "uvicorn.error": {"handlers": ["console"], "level": log_level, "propagate": False},
            "uvicorn.access": {"handlers": ["console"], "level": log_level, "propagate": False},
            "httpx": {"handlers": ["console"], "level": "WARNING", "propagate": False},
            "httpcore": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        },
    }