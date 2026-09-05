"""Structured logging configuration (SAD §8.3, observability).

JSON-line formatter that automatically pulls the active ``request_id`` from the
context variable set by ``RequestIdMiddleware``, so any log call inside a
request handler (route, use case, repository) gets correlated without the
caller passing the id around.

Outside a request (e.g. background workers, startup), ``request_id`` is omitted.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from app.shared.middleware.request_id import get_current_request_id


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log record.

    Standard fields: ``timestamp``, ``level``, ``logger``, ``message``,
    ``request_id`` (when in a request). Any record attribute supplied via
    ``extra=`` is merged into the top-level object; keep them flat and
    machine-readable so ingestion pipelines can index without a parser.
    """

    _RESERVED = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "asctime",
        "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        rid = get_current_request_id()
        if rid is not None:
            payload["request_id"] = rid
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key in self._RESERVED or key.startswith("_"):
                continue
            if key in payload:
                continue
            try:
                json.dumps(value)
            except (TypeError, ValueError):
                value = repr(value)
            payload[key] = value
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Install the JSON formatter on the root logger.

    Idempotent, safe to call from multiple bootstrap paths (FastAPI startup,
    worker scripts, tests). Existing handlers are replaced so the output format
    stays consistent.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())
