"""Pydantic schemas for garments, analysis, try-on, and demo payloads."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Recommendation(str, Enum):
    WORTH_IT = "worth_it"
    THINK_AGAIN = "think_again"
    SKIP_IT = "skip_it"


class TryOnStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProviderMode(str, Enum):
    LIVE = "live"
    DEMO = "demo"
    DISABLED = "disabled"


class Garment(BaseModel):
    id: str
    name: str
    category: str
    subcategory: str
    colors: list[str]
    style_tags: list[str]
    season_tags: list[str]
    occasion_tags: list[str]
    layer: str
    image_url: str
    price: float | None = None
    description: str | None = None
    brand: str | None = None

    @field_validator(
        "colors",
        "style_tags",
        "season_tags",
        "occasion_tags",
        mode="before",
    )
    @classmethod
    def normalize_tags(cls, value: object) -> list[str]:
        if not isinstance(value, list):
            raise ValueError("tag fields must be lists of strings")
        return [str(item).strip().lower() for item in value if str(item).strip()]


class Shopper(BaseModel):
    id: str
    name: str
    photo_url: str
    photo_alt: str
    climate_tags: list[str]
    target_occasions: list[str]
    city: str
    notes: str | None = None


class DemoConfig(BaseModel):
    wear_horizon_months: int = 12
    live_timeout_seconds: int = 20
    target_occasions: list[str] = Field(
        default_factory=lambda: ["work", "weekend", "commute", "evening"]
    )


class CandidateProduct(Garment):
    short_label: str
    demo_role: Literal["duplicative", "versatile", "custom"]
    prepared_try_on_url: str
    prepared_try_on_alt: str
    scenario_assets: list["ScenarioAsset"] = Field(default_factory=list)


class ScenarioAsset(BaseModel):
    id: str
    label: str
    context: str
    image_url: str
    alt: str


class FactorComponent(BaseModel):
    key: str
    label: str
    value: float = Field(ge=0, le=1)
    weight: float
    contribution: float
    explanation: str


class MatchedItem(BaseModel):
    item_id: str
    name: str
    image_url: str
    reason: str
    similarity: float | None = None


class RejectedCombination(BaseModel):
    item_ids: list[str]
    names: list[str]
    rule: str
    reason: str


class OutfitPiece(BaseModel):
    item_id: str
    name: str
    image_url: str
    layer: str


class CompatibleOutfit(BaseModel):
    id: str
    occasion: str
    pieces: list[OutfitPiece]
    rationale: str


class CostPerWearScenario(BaseModel):
    price: float
    estimated_wears: int
    estimated_cpw: float
    horizon_months: int
    formula: str
    assumptions: list[str]


class AnalysisResult(BaseModel):
    candidate_id: str
    candidate_name: str
    recommendation: Recommendation
    recommendation_label: str
    return_risk: int = Field(ge=0, le=100)
    worth_score: int = Field(ge=0, le=100)
    wardrobe_compatibility: int = Field(ge=0, le=100)
    factors: list[FactorComponent]
    matched_items: list[MatchedItem]
    rejected_combinations: list[RejectedCombination]
    outfits: list[CompatibleOutfit]
    outfit_count: int
    cost_per_wear: CostPerWearScenario | None = None
    summary: str
    methodology_notes: list[str]
    is_prototype: bool = True


class AnalyzeRequest(BaseModel):
    candidate_id: str
    climate_tags: list[str] | None = None
    target_occasions: list[str] | None = None
    wear_horizon_months: int | None = Field(default=None, ge=1, le=36)


class TryOnRequest(BaseModel):
    candidate_id: str
    shopper_asset_id: str = "shopper-maya"


class TryOnJob(BaseModel):
    job_id: str
    status: TryOnStatus
    provider: ProviderMode
    result_image_url: str | None = None
    error_category: str | None = None
    error_message: str | None = None
    prepared_fallback_available: bool = False
    prepared_fallback_url: str | None = None
    elapsed_ms: int | None = None


class ScenarioRequest(BaseModel):
    candidate_id: str
    try_on_job_id: str | None = None
    contexts: list[str] = Field(
        default_factory=lambda: ["office", "weekend", "rainy-commute"]
    )


class ScenarioResult(BaseModel):
    enabled: bool
    provider: ProviderMode
    images: list[ScenarioAsset]
    message: str


class HealthResponse(BaseModel):
    status: str
    try_on_mode: ProviderMode
    scenario_mode: ProviderMode
    demo_mode: bool
    mcp_active: bool = False


class DemoPayload(BaseModel):
    shopper: Shopper
    closet: list[Garment]
    candidates: list[CandidateProduct]
    config: DemoConfig
    tagline: str
    pitch: str
    close_line: str
