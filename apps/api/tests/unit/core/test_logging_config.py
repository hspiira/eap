"""Structured-logging formatter tests (Cross-cutting #Observability)."""

import io
import json
import logging

import pytest

from app.core.logging_config import JsonFormatter, configure_logging
from app.shared.middleware.request_id import current_request_id


@pytest.fixture
def captured_handler():
    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("test.json")
    logger.handlers[:] = [handler]
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    yield logger, buffer


class TestJsonFormatter:
    def test_emits_one_json_line_per_record(self, captured_handler):
        logger, buffer = captured_handler
        logger.info("hello world")
        line = buffer.getvalue().strip()
        record = json.loads(line)
        assert record["message"] == "hello world"
        assert record["level"] == "INFO"
        assert record["logger"] == "test.json"
        assert "timestamp" in record

    def test_extra_fields_merged(self, captured_handler):
        logger, buffer = captured_handler
        logger.info("op done", extra={"user_id": "u-1", "duration_ms": 42})
        record = json.loads(buffer.getvalue().strip())
        assert record["user_id"] == "u-1"
        assert record["duration_ms"] == 42

    def test_request_id_appears_when_context_set(self, captured_handler):
        logger, buffer = captured_handler
        token = current_request_id.set("11111111-2222-3333-4444-555555555555")
        try:
            logger.info("inside request")
        finally:
            current_request_id.reset(token)
        record = json.loads(buffer.getvalue().strip())
        assert record["request_id"] == "11111111-2222-3333-4444-555555555555"

    def test_request_id_omitted_when_unset(self, captured_handler):
        logger, buffer = captured_handler
        logger.info("no context")
        record = json.loads(buffer.getvalue().strip())
        assert "request_id" not in record

    def test_exception_serialised(self, captured_handler):
        logger, buffer = captured_handler
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            logger.exception("crash")
        record = json.loads(buffer.getvalue().strip())
        assert "exc_info" in record
        assert "RuntimeError" in record["exc_info"]

    def test_unserialisable_extra_falls_back_to_repr(self, captured_handler):
        logger, buffer = captured_handler
        logger.info("opaque", extra={"thing": object()})
        record = json.loads(buffer.getvalue().strip())
        assert "thing" in record
        assert "object" in record["thing"]


class TestConfigureLogging:
    def test_configure_is_idempotent(self):
        configure_logging("INFO")
        configure_logging("DEBUG")  # second call replaces, doesn't duplicate handlers
        root = logging.getLogger()
        assert len(root.handlers) == 1
        assert root.level == logging.DEBUG
