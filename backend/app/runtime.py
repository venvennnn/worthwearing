"""Shared analysis and try-on orchestration for Streamlit and FastAPI."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

from app.cache import analysis_cache_key, get_cached, set_cached
from app.config import get_settings
from app.models import (
    AnalysisResult,
    CandidateProduct,
    Garment,
    ProviderMode,
    TryOnJob,
    TryOnRequest,
    TryOnStatus,
)
from app.providers.demo import DemoProvider
from app.providers.perfect_corp import PerfectCorpProvider
from app.scoring import ScoreInputs, analyze
from app.store import catalog_overlay, closet_fingerprint, get_candidate, load_demo, resolve_asset_path

LIVE_TIMEOUT_SECONDS = 45


def try_on_mode() -> ProviderMode:
    settings = get_settings()
    if settings.demo_mode or not settings.live_try_on_configured:
        return ProviderMode.DEMO
    return ProviderMode.LIVE


def provider_label() -> str:
    return "Live API" if try_on_mode() == ProviderMode.LIVE else "Prepared demo"


def asset_path(image_url: str) -> Path | None:
    return resolve_asset_path(image_url)


def image_source(image_url: str) -> str | Path:
    local = asset_path(image_url)
    return local if local is not None else image_url


def analyze_candidate(
    candidate_id: str,
    extra_closet: list[Garment] | None = None,
    extra_candidates: list[CandidateProduct] | None = None,
) -> AnalysisResult:
    with catalog_overlay(extra_closet, extra_candidates):
        demo = load_demo()
        candidate = get_candidate(candidate_id)
        cache_key = analysis_cache_key(
            demo.shopper.id,
            candidate.id,
            demo.shopper.climate_tags,
            demo.config.target_occasions,
            demo.config.wear_horizon_months,
            closet_fingerprint(demo.closet),
        )
        cached = get_cached(cache_key)
        if cached:
            return AnalysisResult.model_validate(cached)
        result = analyze(
            ScoreInputs(
                candidate=candidate,
                closet=demo.closet,
                climate_tags=demo.shopper.climate_tags,
                target_occasions=demo.config.target_occasions,
                wear_horizon_months=demo.config.wear_horizon_months,
            )
        )
        set_cached(cache_key, result.model_dump(mode="json"))
        return result


async def _run_try_on(candidate_id: str) -> TryOnJob:
    settings = get_settings()
    request = TryOnRequest(candidate_id=candidate_id, shopper_asset_id="shopper-maya")
    request_id = f"ui-{candidate_id}"
    if try_on_mode() == ProviderMode.LIVE:
        provider: DemoProvider | PerfectCorpProvider = PerfectCorpProvider(settings)
    else:
        provider = DemoProvider()
    job = await provider.create_try_on(request, request_id)
    if job.status in {TryOnStatus.FAILED, TryOnStatus.COMPLETED}:
        return job
    started = time.perf_counter()
    while job.status in {TryOnStatus.QUEUED, TryOnStatus.PROCESSING}:
        if time.perf_counter() - started > LIVE_TIMEOUT_SECONDS:
            return job.model_copy(
                update={
                    "error_category": job.error_category or "timeout",
                    "error_message": job.error_message
                    or "Live try-on exceeded 45 seconds.",
                }
            )
        await asyncio.sleep(0.8)
        job = await provider.get_status(job.job_id, request_id)
    return job


def run_try_on(
    candidate_id: str,
    extra_closet: list[Garment] | None = None,
    extra_candidates: list[CandidateProduct] | None = None,
) -> TryOnJob:
    with catalog_overlay(extra_closet, extra_candidates):
        return asyncio.run(_run_try_on(candidate_id))


def prepared_result(
    candidate_id: str,
    extra_closet: list[Garment] | None = None,
    extra_candidates: list[CandidateProduct] | None = None,
) -> TryOnJob:
    with catalog_overlay(extra_closet, extra_candidates):
        candidate = get_candidate(candidate_id)
        return TryOnJob(
            job_id=f"demo-{candidate_id}",
            status=TryOnStatus.COMPLETED,
            provider=ProviderMode.DEMO,
            result_image_url=candidate.prepared_try_on_url,
            prepared_fallback_available=True,
            prepared_fallback_url=candidate.prepared_try_on_url,
        )
