"""Tests for structured logging with correlation IDs."""

import json
import logging

from simpro_client.logging import (
    JSONFormatter,
    configure_logging,
    correlation_id_var,
    get_correlation_id,
    set_correlation_id,
)


def test_set_and_get_correlation_id():
    """Correlation ID can be set and retrieved."""
    cid = set_correlation_id("test-123")
    assert cid == "test-123"
    assert get_correlation_id() == "test-123"
    # Reset for other tests
    correlation_id_var.set("")


def test_auto_generate_correlation_id():
    """A new correlation ID is generated if none is set."""
    correlation_id_var.set("")  # Clear any existing ID
    cid = get_correlation_id()
    assert isinstance(cid, str) and len(cid) == 12
    # Reset for other tests
    correlation_id_var.set("")


def test_json_formatter_includes_correlation_id():
    """JSON formatter includes the correlation ID in output."""
    set_correlation_id("log-test-id")
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="simpro_client",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test message",
        args=None,
        exc_info=None,
    )
    output = formatter.format(record)
    data = json.loads(output)
    assert data["correlation_id"] == "log-test-id"
    assert data["message"] == "Test message"
    assert data["level"] == "INFO"
    # Reset
    correlation_id_var.set("")


def test_json_formatter_includes_request_fields():
    """JSON formatter includes HTTP request fields when present."""
    set_correlation_id("req-test")
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="simpro_client",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="GET /companies/1/jobs/ -> 200",
        args=None,
        exc_info=None,
    )
    record.method = "GET"
    record.url = "/companies/1/jobs/"
    record.status_code = 200
    record.duration_ms = 45.2
    output = formatter.format(record)
    data = json.loads(output)
    assert data["method"] == "GET"
    assert data["url"] == "/companies/1/jobs/"
    assert data["status_code"] == 200
    assert data["duration_ms"] == 45.2
    # Reset
    correlation_id_var.set("")


def test_configure_logging_returns_logger():
    """configure_logging returns a configured logger."""
    logger = configure_logging(level="DEBUG")
    assert logger.name == "simpro_client"
    assert logger.level == logging.DEBUG
