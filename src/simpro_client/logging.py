"""Structured logging configuration with correlation ID support."""

import json
import logging
import time
import uuid
from contextvars import ContextVar
from typing import Any

# Thread-safe variable that holds the current correlation ID
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Get the current correlation ID or generate a new one."""
    cid = correlation_id_var.get()
    if not cid:
        cid = uuid.uuid4().hex[:12]
        correlation_id_var.set(cid)
    return cid


def set_correlation_id(cid: str | None = None) -> str:
    """Set a correlation ID for the current context."""
    if cid is None:
        cid = uuid.uuid4().hex[:12]
    correlation_id_var.set(cid)
    return cid


class JSONFormatter(logging.Formatter):
    """Format log records as JSON with correlation IDs."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_var.get(""),
        }
        # Include HTTP fields when present on the log record
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "url"):
            log_data["url"] = record.url
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def configure_logging(level: str = "INFO") -> logging.Logger:
    """Configure structured JSON logging for the simpro_client package."""
    logger = logging.getLogger("simpro_client")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    return logger


class RequestTimer:
    """Context manager for timing HTTP requests."""

    def __init__(self) -> None:
        self.start_time: float = 0.0
        self.duration_ms: float = 0.0

    def __enter__(self) -> "RequestTimer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        self.duration_ms = (time.perf_counter() - self.start_time) * 1000
