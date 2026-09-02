"""Prepared-asset try-on provider used when live API is off or as an explicit fallback."""

from __future__ import annotations

import asyncio
import time
import uuid
from threading import Lock

from app.logging_utils import log_event
from app.models import ProviderMode, TryOnJob, TryOnRequest, TryOnStatus
from app.providers.base import VirtualTryOnProvider
from app.store import get_candidate

_jobs: dict[str, TryOnJob] = {}
_created_at: dict[str, float] = {}
_lock = Lock()


class DemoProvider(VirtualTryOnProvider):
    mode = ProviderMode.DEMO

    def __init__(self, processing_delay_seconds: float = 1.4) -> None:
        self.processing_delay_seconds = processing_delay_seconds

    async def create_try_on(self, request: TryOnRequest, request_id: str) -> TryOnJob:
        started = time.perf_counter()
        candidate = get_candidate(request.candidate_id)
        job_id = f"demo-{uuid.uuid4()}"
        job = TryOnJob(
            job_id=job_id,
            status=TryOnStatus.QUEUED,
            provider=ProviderMode.DEMO,
            prepared_fallback_available=True,
            prepared_fallback_url=candidate.prepared_try_on_url,
        )
        with _lock:
            _jobs[job_id] = job
            _created_at[job_id] = time.perf_counter()
        log_event(
            request_id=request_id,
            provider="demo",
            latency_ms=int((time.perf_counter() - started) * 1000),
            status="queued",
            extra={"job_id": job_id, "candidate_id": request.candidate_id},
        )
        return job

    async def get_status(self, job_id: str, request_id: str) -> TryOnJob:
        started = time.perf_counter()
        with _lock:
            job = _jobs.get(job_id)
            created = _created_at.get(job_id, 0.0)
        if job is None:
            return TryOnJob(
                job_id=job_id,
                status=TryOnStatus.FAILED,
                provider=ProviderMode.DEMO,
                error_category="not_found",
                error_message="Unknown try-on job.",
            )
        elapsed = time.perf_counter() - created
        if elapsed < 0.35:
            status = TryOnStatus.QUEUED
        elif elapsed < self.processing_delay_seconds:
            status = TryOnStatus.PROCESSING
            await asyncio.sleep(0)
        else:
            status = TryOnStatus.COMPLETED
        updated = job.model_copy(
            update={
                "status": status,
                "result_image_url": job.prepared_fallback_url
                if status == TryOnStatus.COMPLETED
                else None,
                "elapsed_ms": int(elapsed * 1000),
            }
        )
        with _lock:
            _jobs[job_id] = updated
        log_event(
            request_id=request_id,
            provider="demo",
            latency_ms=int((time.perf_counter() - started) * 1000),
            status=status.value,
            extra={"job_id": job_id},
        )
        return updated
