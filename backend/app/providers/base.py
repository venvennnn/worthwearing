"""Virtual try-on provider contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import ProviderMode, TryOnJob, TryOnRequest


class VirtualTryOnProvider(ABC):
    mode: ProviderMode

    @abstractmethod
    async def create_try_on(self, request: TryOnRequest, request_id: str) -> TryOnJob:
        """Start or return a try-on job."""

    @abstractmethod
    async def get_status(self, job_id: str, request_id: str) -> TryOnJob:
        """Return queued, processing, completed, or failed."""
