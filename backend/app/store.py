"""Load curated demo JSON. No database."""

from __future__ import annotations

import json
from functools import lru_cache

from app.config import DATA_DIR
from app.models import CandidateProduct, DemoConfig, DemoPayload, Garment, Shopper


@lru_cache
def load_closet() -> list[Garment]:
    raw = json.loads((DATA_DIR / "closet.json").read_text(encoding="utf-8"))
    return [Garment.model_validate(item) for item in raw]


@lru_cache
def load_candidates() -> list[CandidateProduct]:
    raw = json.loads((DATA_DIR / "products.json").read_text(encoding="utf-8"))
    return [CandidateProduct.model_validate(item) for item in raw]


@lru_cache
def load_demo() -> DemoPayload:
    raw = json.loads((DATA_DIR / "demo.json").read_text(encoding="utf-8"))
    return DemoPayload(
        shopper=Shopper.model_validate(raw["shopper"]),
        closet=load_closet(),
        candidates=load_candidates(),
        config=DemoConfig.model_validate(raw["config"]),
        tagline=raw["tagline"],
        pitch=raw["pitch"],
        close_line=raw["close_line"],
    )


def get_candidate(candidate_id: str) -> CandidateProduct:
    for item in load_candidates():
        if item.id == candidate_id:
            return item
    raise KeyError(candidate_id)
