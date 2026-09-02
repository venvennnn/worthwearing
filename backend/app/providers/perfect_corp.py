"""Perfect Corp AI Clothes Virtual Try-On adapter.

Official contract (YouCam Online Editor, cloth-v4):

  POST {PERFECT_CORP_BASE_URL}{PERFECT_CORP_TRYON_PATH}
  Authorization: Bearer {PERFECT_CORP_API_KEY}
  JSON body — insert documented fields here:
    src_file_url or src_file_id   shopper / person image
    ref_file_url or ref_file_id   garment / outfit reference
    garment_category              upper | lower | full_body | etc.

  Response: { "status": 200, "data": { "task_id": "..." } }

  GET {PERFECT_CORP_BASE_URL}{PERFECT_CORP_STATUS_PATH}  with {task_id}
  Success: data.task_status == "success" and data.results.url
  Error:   data.task_status == "error" or HTTP 4xx/5xx

All request mapping is isolated in this file. If Perfect Corp changes field
names, update `_build_try_on_payload` and `_normalize_status` only.
Secrets never leave the server.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from threading import Lock

import httpx

from app.config import Settings, get_settings
from app.logging_utils import log_event
from app.models import ProviderMode, TryOnJob, TryOnRequest, TryOnStatus
from app.providers.base import VirtualTryOnProvider
from app.store import get_candidate, load_demo

_jobs: dict[str, TryOnJob] = {}
_remote_ids: dict[str, str] = {}
_lock = Lock()

TRANSIENT_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


class PerfectCorpProvider(VirtualTryOnProvider):
    mode = ProviderMode.LIVE

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _headers(self) -> dict[str, str]:
        key = self.settings.perfect_corp_api_key or ""
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _build_try_on_payload(self, request: TryOnRequest) -> dict[str, str]:
        demo = load_demo()
        candidate = get_candidate(request.candidate_id)
        shopper_url = demo.shopper.photo_url
        if shopper_url.startswith("/"):
            shopper_url = f"{self.settings.cors_origins[0]}{shopper_url}"
        garment_url = candidate.image_url
        if garment_url.startswith("/"):
            garment_url = f"{self.settings.cors_origins[0]}{garment_url}"
        # Official payload fields for cloth-v4. Swap in src_file_id / ref_file_id
        # if the deployment uses the File API instead of public URLs.
        return {
            "src_file_url": shopper_url,
            "ref_file_url": garment_url,
            "garment_category": "upper",
        }

    def _normalize_create(self, body: dict) -> str:
        data = body.get("data") if isinstance(body.get("data"), dict) else body
        task_id = data.get("task_id") or data.get("id") or body.get("task_id")
        if not task_id:
            raise ValueError("missing_task_id")
        return str(task_id)

    def _normalize_status(self, body: dict, job: TryOnJob) -> TryOnJob:
        data = body.get("data") if isinstance(body.get("data"), dict) else body
        remote_status = str(
            data.get("task_status") or data.get("status") or ""
        ).lower()
        error = data.get("error")
        results = data.get("results") or {}
        result_url = None
        if isinstance(results, dict):
            result_url = results.get("url") or results.get("result_url")
        elif isinstance(results, list) and results:
            first = results[0]
            if isinstance(first, dict):
                result_url = first.get("url")
            elif isinstance(first, str):
                result_url = first

        if remote_status in {"success", "succeeded", "completed", "done"} and result_url:
            return job.model_copy(
                update={
                    "status": TryOnStatus.COMPLETED,
                    "result_image_url": result_url,
                    "error_category": None,
                    "error_message": None,
                }
            )
        if remote_status in {"error", "failed", "fail"} or error:
            return job.model_copy(
                update={
                    "status": TryOnStatus.FAILED,
                    "error_category": "provider_error",
                    "error_message": str(error or "Perfect Corp task failed."),
                }
            )
        if remote_status in {"queued", "pending", "created"}:
            return job.model_copy(update={"status": TryOnStatus.QUEUED})
        return job.model_copy(update={"status": TryOnStatus.PROCESSING})

    async def _request_with_retry(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        last_error: Exception | None = None
        attempts = 1 + self.settings.max_retries
        for attempt in range(attempts):
            try:
                response = await client.request(method, url, **kwargs)
                if response.status_code in TRANSIENT_STATUS and attempt < attempts - 1:
                    await asyncio.sleep(0.4 * (attempt + 1))
                    continue
                return response
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                if attempt < attempts - 1:
                    await asyncio.sleep(0.4 * (attempt + 1))
                    continue
                raise
        if last_error:
            raise last_error
        raise RuntimeError("retry_exhausted")

    async def create_try_on(self, request: TryOnRequest, request_id: str) -> TryOnJob:
        started = time.perf_counter()
        candidate = get_candidate(request.candidate_id)
        job_id = f"live-{uuid.uuid4()}"
        job = TryOnJob(
            job_id=job_id,
            status=TryOnStatus.QUEUED,
            provider=ProviderMode.LIVE,
            prepared_fallback_available=True,
            prepared_fallback_url=candidate.prepared_try_on_url,
        )
        url = (
            self.settings.perfect_corp_base_url.rstrip("/")
            + self.settings.perfect_corp_tryon_path
        )
        try:
            timeout = httpx.Timeout(self.settings.request_timeout_seconds)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await self._request_with_retry(
                    client,
                    "POST",
                    url,
                    headers=self._headers(),
                    json=self._build_try_on_payload(request),
                )
            if response.status_code >= 400:
                category = "auth" if response.status_code in {401, 403} else "http_error"
                job = job.model_copy(
                    update={
                        "status": TryOnStatus.FAILED,
                        "error_category": category,
                        "error_message": "Live try-on could not be started.",
                    }
                )
            else:
                remote_id = self._normalize_create(response.json())
                with _lock:
                    _remote_ids[job_id] = remote_id
        except httpx.TimeoutException:
            job = job.model_copy(
                update={
                    "status": TryOnStatus.FAILED,
                    "error_category": "timeout",
                    "error_message": "Live try-on timed out.",
                }
            )
        except Exception:
            job = job.model_copy(
                update={
                    "status": TryOnStatus.FAILED,
                    "error_category": "network",
                    "error_message": "Live try-on is unavailable.",
                }
            )
        with _lock:
            _jobs[job_id] = job
        log_event(
            request_id=request_id,
            provider="perfect_corp",
            latency_ms=int((time.perf_counter() - started) * 1000),
            status=job.status.value,
            error_category=job.error_category,
            extra={"job_id": job_id, "candidate_id": request.candidate_id},
        )
        return job

    async def get_status(self, job_id: str, request_id: str) -> TryOnJob:
        started = time.perf_counter()
        with _lock:
            job = _jobs.get(job_id)
            remote_id = _remote_ids.get(job_id)
        if job is None:
            return TryOnJob(
                job_id=job_id,
                status=TryOnStatus.FAILED,
                provider=ProviderMode.LIVE,
                error_category="not_found",
                error_message="Unknown try-on job.",
            )
        if job.status in {TryOnStatus.COMPLETED, TryOnStatus.FAILED}:
            return job
        if not remote_id:
            return job.model_copy(
                update={
                    "status": TryOnStatus.FAILED,
                    "error_category": "missing_remote_id",
                    "error_message": "Live job has no provider task id.",
                }
            )
        path = self.settings.perfect_corp_status_path.replace("{task_id}", remote_id)
        if "{task_id}" not in self.settings.perfect_corp_status_path:
            path = self.settings.perfect_corp_status_path.rstrip("/") + f"/{remote_id}"
        url = self.settings.perfect_corp_base_url.rstrip("/") + path
        try:
            timeout = httpx.Timeout(self.settings.request_timeout_seconds)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await self._request_with_retry(
                    client, "GET", url, headers=self._headers()
                )
            if response.status_code >= 400:
                job = job.model_copy(
                    update={
                        "status": TryOnStatus.FAILED,
                        "error_category": "http_error",
                        "error_message": "Could not read live try-on status.",
                    }
                )
            else:
                job = self._normalize_status(response.json(), job)
        except httpx.TimeoutException:
            job = job.model_copy(
                update={
                    "status": TryOnStatus.FAILED,
                    "error_category": "timeout",
                    "error_message": "Live try-on status timed out.",
                }
            )
        except Exception:
            job = job.model_copy(
                update={
                    "status": TryOnStatus.FAILED,
                    "error_category": "network",
                    "error_message": "Live try-on status is unavailable.",
                }
            )
        with _lock:
            _jobs[job_id] = job
        log_event(
            request_id=request_id,
            provider="perfect_corp",
            latency_ms=int((time.perf_counter() - started) * 1000),
            status=job.status.value,
            error_category=job.error_category,
            extra={"job_id": job_id},
        )
        return job
