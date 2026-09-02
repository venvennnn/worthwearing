"""WorthWearing FastAPI application."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse

from app.cache import analysis_cache_key, get_cached, set_cached
from app.config import DATA_DIR, get_settings
from app.logging_utils import configure_logging, log_event, new_request_id
from app.models import (
    AnalysisResult,
    AnalyzeRequest,
    DemoPayload,
    HealthResponse,
    ProviderMode,
    ScenarioRequest,
    ScenarioResult,
    TryOnJob,
    TryOnRequest,
)
from app.providers.demo import DemoProvider
from app.providers.perfect_corp import PerfectCorpProvider
from app.providers.scenarios import OptionalMcpAdapter, ScenarioImageProvider
from app.scoring import ScoreInputs, analyze
from app.store import get_candidate, load_demo

configure_logging()
settings = get_settings()
demo_provider = DemoProvider()
live_provider = PerfectCorpProvider(settings)
scenario_provider = ScenarioImageProvider(settings)
mcp_adapter = OptionalMcpAdapter()


def try_on_mode() -> ProviderMode:
    if settings.demo_mode or not settings.live_try_on_configured:
        return ProviderMode.DEMO
    return ProviderMode.LIVE


def scenario_mode() -> ProviderMode:
    if scenario_provider.enabled:
        return ProviderMode.LIVE
    return ProviderMode.DISABLED


@asynccontextmanager
async def lifespan(_: FastAPI):
    load_demo()
    yield


app = FastAPI(
    title="WorthWearing Intelligence",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
)

assets_dir = DATA_DIR / "assets"
assets_dir.mkdir(parents=True, exist_ok=True)
app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.middleware("http")
async def attach_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or new_request_id()
    started = time.perf_counter()
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    if not request.url.path.startswith("/assets"):
        log_event(
            request_id=request_id,
            provider="api",
            latency_ms=int((time.perf_counter() - started) * 1000),
            status=str(response.status_code),
            extra={"path": request.url.path, "method": request.method},
        )
    return response


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        try_on_mode=try_on_mode(),
        scenario_mode=scenario_mode(),
        demo_mode=settings.demo_mode or not settings.live_try_on_configured,
        mcp_active=mcp_adapter.active,
    )


@app.get("/api/demo", response_model=DemoPayload)
async def demo_payload() -> DemoPayload:
    return load_demo()


@app.post("/api/analyze", response_model=AnalysisResult)
async def analyze_candidate(body: AnalyzeRequest, request: Request) -> AnalysisResult:
    demo = load_demo()
    try:
        candidate = get_candidate(body.candidate_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown candidate.") from exc

    climate = body.climate_tags or demo.shopper.climate_tags
    occasions = body.target_occasions or demo.config.target_occasions
    horizon = body.wear_horizon_months or demo.config.wear_horizon_months
    cache_key = analysis_cache_key(
        demo.shopper.id, candidate.id, climate, occasions, horizon
    )
    cached = get_cached(cache_key)
    if cached:
        return AnalysisResult.model_validate(cached)

    result = analyze(
        ScoreInputs(
            candidate=candidate,
            closet=demo.closet,
            climate_tags=climate,
            target_occasions=occasions,
            wear_horizon_months=horizon,
        )
    )
    set_cached(cache_key, result.model_dump(mode="json"))
    log_event(
        request_id=request.state.request_id,
        provider="scoring",
        latency_ms=0,
        status="ok",
        extra={"candidate_id": candidate.id, "return_risk": result.return_risk},
    )
    return result


@app.post("/api/try-on", response_model=TryOnJob)
async def create_try_on(body: TryOnRequest, request: Request) -> TryOnJob:
    try:
        get_candidate(body.candidate_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown candidate.") from exc
    provider = live_provider if try_on_mode() == ProviderMode.LIVE else demo_provider
    return await provider.create_try_on(body, request.state.request_id)


@app.get("/api/try-on/{job_id}", response_model=TryOnJob)
async def get_try_on(job_id: str, request: Request) -> TryOnJob:
    if job_id.startswith("demo-"):
        return await demo_provider.get_status(job_id, request.state.request_id)
    if job_id.startswith("live-"):
        return await live_provider.get_status(job_id, request.state.request_id)
    raise HTTPException(status_code=404, detail="Unknown try-on job.")


@app.post("/api/try-on/{job_id}/fallback", response_model=TryOnJob)
async def use_prepared_fallback(job_id: str, request: Request) -> TryOnJob:
    """Explicit fallback — never substituted silently."""
    if job_id.startswith("live-"):
        current = await live_provider.get_status(job_id, request.state.request_id)
    elif job_id.startswith("demo-"):
        current = await demo_provider.get_status(job_id, request.state.request_id)
    else:
        raise HTTPException(status_code=404, detail="Unknown try-on job.")
    if not current.prepared_fallback_url:
        raise HTTPException(status_code=409, detail="No prepared demo result is available.")
    return current.model_copy(
        update={
            "status": "completed",
            "provider": ProviderMode.DEMO,
            "result_image_url": current.prepared_fallback_url,
            "error_category": None,
            "error_message": None,
        }
    )


@app.post("/api/scenarios", response_model=ScenarioResult)
async def create_scenarios(body: ScenarioRequest, request: Request) -> ScenarioResult:
    try:
        get_candidate(body.candidate_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown candidate.") from exc
    return await scenario_provider.create_scenarios(body, request.state.request_id)


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        raise exc
    log_event(
        request_id=getattr(request.state, "request_id", "unknown"),
        provider="api",
        latency_ms=0,
        status="500",
        error_category=type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal error.", "error_category": type(exc).__name__},
    )
