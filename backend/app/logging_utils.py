"""Structured request logging. Never log keys or image bytes."""

from __future__ import annotations

import logging
import uuid
from typing import Any

logger = logging.getLogger("worthwearing")


def configure_logging() -> None:
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def new_request_id() -> str:
    return str(uuid.uuid4())


def log_event(
    *,
    request_id: str,
    provider: str,
    latency_ms: int,
    status: str,
    error_category: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    payload = {
        "request_id": request_id,
        "provider": provider,
        "latency_ms": latency_ms,
        "status": status,
        "error_category": error_category,
    }
    if extra:
        redacted = {
            key: value
            for key, value in extra.items()
            if key.lower() not in {"api_key", "authorization", "token", "image_bytes"}
        }
        payload.update(redacted)
    logger.info(" ".join(f"{k}={v}" for k, v in payload.items()))
