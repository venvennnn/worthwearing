"""Perfect Corp AI Clothes Virtual Try-On adapter.

Official contract (YouCam Online Editor):

  1) File API — local assets are not public, so we upload bytes:
     POST {BASE}/s2s/v2.0/file
     { "files": [{ "content_type", "file_name", "file_size" }] }
     then PUT the image to data.files[0].requests[0].url

  2) Create task:
     POST {BASE}{PERFECT_CORP_TRYON_PATH}   default /s2s/v2.0/task/cloth-v4
     Official JSON fields (insert here if the console contract changes):
       src_file_id or src_file_url
       ref_file_id or ref_file_url
       garment_category   outer | upper | lower | full_body

  3) Poll:
     GET {BASE}{PERFECT_CORP_STATUS_PATH}  with {task_id}
     success: data.task_status == "success" and data.results.url

Secrets never leave the server. Do not log keys or image bytes.
"""

from __future__ import annotations

import asyncio
import mimetypes
import time
import uuid
from pathlib import Path
from threading import Lock

import httpx

from app.catalog import garment_category_for
from app.config import Settings, get_settings
from app.logging_utils import log_event
from app.models import ProviderMode, TryOnJob, TryOnRequest, TryOnStatus
from app.providers.base import VirtualTryOnProvider
from app.store import get_candidate, load_demo, resolve_asset_path

_jobs: dict[str, TryOnJob] = {}
_remote_ids: dict[str, str] = {}
_file_ids: dict[str, str] = {}
_lock = Lock()

TRANSIENT_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}
FILE_API_PATH = "/s2s/v2.0/file"


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

    def _asset_path(self, image_url: str) -> Path:
        path = resolve_asset_path(image_url)
        if path is None:
            name = image_url.rsplit("/", 1)[-1]
            raise FileNotFoundError(name)
        return path

    def _task_payload(
        self,
        src_file_id: str,
        ref_file_id: str,
        garment_category: str = "outer",
    ) -> dict[str, str]:
        # Official cloth-v4 fields. Use src_file_url / ref_file_url only when
        # the image is already hosted on a public URL Perfect Corp can fetch.
        return {
            "src_file_id": src_file_id,
            "ref_file_id": ref_file_id,
            "garment_category": garment_category,
        }

    def _normalize_create(self, body: dict) -> str:
        data = body.get("data") if isinstance(body.get("data"), dict) else body
        task_id = data.get("task_id") or data.get("id") or body.get("task_id")
        if not task_id:
            raise ValueError("missing_task_id")
        return str(task_id)

    def _provider_error_message(self, response: httpx.Response) -> str:
        try:
            body = response.json()
        except Exception:
            return "Live try-on could not be started."
        code = body.get("error_code") or body.get("error")
        data = body.get("data") if isinstance(body.get("data"), dict) else {}
        nested = data.get("error") or data.get("error_code")
        detail = nested or code
        if detail:
            return f"Perfect Corp error: {detail}"
        return "Live try-on could not be started."

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

    async def _upload_asset(self, client: httpx.AsyncClient, image_url: str) -> str:
        path = self._asset_path(image_url)
        cache_key = str(path.resolve())
        with _lock:
            cached = _file_ids.get(cache_key)
        if cached:
            return cached

        data = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "image/png"
        reserve_url = self.settings.perfect_corp_base_url.rstrip("/") + FILE_API_PATH
        reserve = await self._request_with_retry(
            client,
            "POST",
            reserve_url,
            headers=self._headers(),
            json={
                "files": [
                    {
                        "content_type": content_type,
                        "file_name": path.name,
                        "file_size": len(data),
                    }
                ]
            },
        )
        if reserve.status_code >= 400:
            raise RuntimeError(f"file_reserve_{reserve.status_code}")
        body = reserve.json()
        files = (body.get("data") or {}).get("files") or []
        if not files:
            raise RuntimeError("file_reserve_empty")
        file_id = files[0].get("file_id")
        requests = files[0].get("requests") or []
        if not file_id or not requests:
            raise RuntimeError("file_reserve_malformed")
        upload = requests[0]
        put_headers = {
            key: str(value)
            for key, value in (upload.get("headers") or {}).items()
            if str(key).lower() not in {"authorization"}
        }
        put_headers.setdefault("Content-Type", content_type)
        put_headers["Content-Length"] = str(len(data))
        put_response = await self._request_with_retry(
            client,
            upload.get("method") or "PUT",
            upload["url"],
            headers=put_headers,
            content=data,
        )
        if put_response.status_code >= 400:
            raise RuntimeError(f"file_upload_{put_response.status_code}")
        with _lock:
            _file_ids[cache_key] = str(file_id)
        return str(file_id)

    async def _build_try_on_payload(
        self, client: httpx.AsyncClient, request: TryOnRequest
    ) -> dict[str, str]:
        demo = load_demo()
        candidate = get_candidate(request.candidate_id)
        src_id = await self._upload_asset(client, demo.shopper.photo_url)
        ref_id = await self._upload_asset(client, candidate.image_url)
        return self._task_payload(
            src_id, ref_id, garment_category_for(candidate)
        )

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
                payload = await self._build_try_on_payload(client, request)
                response = await self._request_with_retry(
                    client,
                    "POST",
                    url,
                    headers=self._headers(),
                    json=payload,
                )
            if response.status_code >= 400:
                category = "auth" if response.status_code in {401, 403} else "http_error"
                job = job.model_copy(
                    update={
                        "status": TryOnStatus.FAILED,
                        "error_category": category,
                        "error_message": self._provider_error_message(response),
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
        except Exception as exc:
            job = job.model_copy(
                update={
                    "status": TryOnStatus.FAILED,
                    "error_category": "network",
                    "error_message": f"Live try-on is unavailable ({type(exc).__name__}).",
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
        path = self.settings.perfect_corp_status_path
        if "{task_id}" in path:
            path = path.replace("{task_id}", remote_id)
        else:
            path = path.rstrip("/") + f"/{remote_id}"
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
                        "error_message": self._provider_error_message(response),
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
