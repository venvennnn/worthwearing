"""In-memory analysis cache keyed by shopper and product hash."""

from __future__ import annotations

import hashlib
from threading import Lock
from typing import Any

_lock = Lock()
_cache: dict[str, dict[str, Any]] = {}


def analysis_cache_key(
    shopper_id: str,
    candidate_id: str,
    climate_tags: list[str],
    target_occasions: list[str],
    horizon: int,
    closet_fingerprint: str = "",
) -> str:
    payload = "|".join(
        [
            shopper_id,
            candidate_id,
            ",".join(sorted(climate_tags)),
            ",".join(sorted(target_occasions)),
            str(horizon),
            closet_fingerprint,
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_cached(key: str) -> dict[str, Any] | None:
    with _lock:
        return _cache.get(key)


def set_cached(key: str, value: dict[str, Any]) -> None:
    with _lock:
        _cache[key] = value
