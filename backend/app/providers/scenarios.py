"""Optional Perfect Corp Image Generator adapter for occasion scenarios.

Disabled automatically when credentials or the image-generator path are absent.
UI must hide scenario generation when `enabled` is false.

Official contract (YouCam Image Generator v2, image-to-image):

  POST {BASE}{PERFECT_CORP_IMAGE_GENERATOR_PATH}
  Authorization: Bearer {KEY}
  JSON — insert documented fields here:
    src_file_urls or src_file_ids
    prompt / style fields per current Image Generator docs

Prepared demo images are returned only when the caller explicitly requests
the demo path; this adapter does not silently substitute them for live output.
"""

from __future__ import annotations

import time

import httpx

from app.config import Settings, get_settings
from app.logging_utils import log_event
from app.models import ProviderMode, ScenarioAsset, ScenarioRequest, ScenarioResult
from app.store import get_candidate


class ScenarioImageProvider:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def enabled(self) -> bool:
        return self.settings.scenario_configured and not self.settings.demo_mode

    async def create_scenarios(
        self, request: ScenarioRequest, request_id: str
    ) -> ScenarioResult:
        candidate = get_candidate(request.candidate_id)
        started = time.perf_counter()
        if not self.enabled:
            log_event(
                request_id=request_id,
                provider="scenario_disabled",
                latency_ms=int((time.perf_counter() - started) * 1000),
                status="disabled",
            )
            return ScenarioResult(
                enabled=False,
                provider=ProviderMode.DISABLED,
                images=[],
                message="Image Generator is not configured, so scenario generation is off.",
            )

        timeout = httpx.Timeout(self.settings.request_timeout_seconds)
        url = (
            self.settings.perfect_corp_base_url.rstrip("/")
            + self.settings.perfect_corp_image_generator_path
        )
        images: list[ScenarioAsset] = []
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                for context in request.contexts:
                    # Official image-to-image fields. Extend if the console
                    # contract adds prompt or style_id requirements.
                    payload = {
                        "src_file_urls": [
                            candidate.prepared_try_on_url
                            if candidate.prepared_try_on_url.startswith("http")
                            else f"{self.settings.cors_origins[0]}{candidate.prepared_try_on_url}"
                        ],
                        "prompt": (
                            f"Keep the same person and navy field jacket. "
                            f"Place them in a photorealistic {context} setting."
                        ),
                    }
                    response = await client.post(
                        url,
                        headers={
                            "Authorization": f"Bearer {self.settings.perfect_corp_api_key}",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )
                    if response.status_code >= 400:
                        raise RuntimeError(f"scenario_http_{response.status_code}")
                    body = response.json()
                    data = body.get("data") if isinstance(body.get("data"), dict) else body
                    task_id = data.get("task_id")
                    if not task_id:
                        raise RuntimeError("missing_task_id")
                    status_url = url.rstrip("/") + f"/{task_id}"
                    status_response = await client.get(
                        status_url,
                        headers={
                            "Authorization": f"Bearer {self.settings.perfect_corp_api_key}",
                            "Accept": "application/json",
                        },
                    )
                    status_body = status_response.json()
                    status_data = (
                        status_body.get("data")
                        if isinstance(status_body.get("data"), dict)
                        else status_body
                    )
                    results = status_data.get("results") or {}
                    result_url = None
                    if isinstance(results, dict):
                        result_url = results.get("url")
                    if result_url:
                        images.append(
                            ScenarioAsset(
                                id=f"{candidate.id}-{context}",
                                label=context.replace("-", " ").title(),
                                context=context,
                                image_url=result_url,
                                alt=f"Generated {context} scenario for {candidate.name}.",
                            )
                        )
            log_event(
                request_id=request_id,
                provider="perfect_corp_image_generator",
                latency_ms=int((time.perf_counter() - started) * 1000),
                status="ok" if images else "empty",
            )
            if not images:
                return ScenarioResult(
                    enabled=True,
                    provider=ProviderMode.LIVE,
                    images=[],
                    message="Image Generator returned no images yet. Prepared scenarios stay available as labeled demo assets.",
                )
            return ScenarioResult(
                enabled=True,
                provider=ProviderMode.LIVE,
                images=images,
                message="Live Image Generator scenarios.",
            )
        except Exception:
            log_event(
                request_id=request_id,
                provider="perfect_corp_image_generator",
                latency_ms=int((time.perf_counter() - started) * 1000),
                status="error",
                error_category="provider_error",
            )
            return ScenarioResult(
                enabled=True,
                provider=ProviderMode.LIVE,
                images=[],
                message="Image Generator call failed. No live scenarios were invented.",
            )


class OptionalMcpAdapter:
    """Optional MCP wrapper behind the same try-on interface.

    MCP is never reported as active unless a real MCP tool call succeeds.
    The application functions through REST or demo mode without this adapter.
    """

    def __init__(self) -> None:
        self.last_mcp_success = False

    @property
    def active(self) -> bool:
        return self.last_mcp_success
