"""Load curated demo JSON and optional per-request catalog overlays."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from contextvars import ContextVar, Token
from functools import lru_cache
from pathlib import Path
from typing import Iterator

from app.catalog import upload_search_dirs
from app.config import DATA_DIR
from app.models import CandidateProduct, DemoConfig, DemoPayload, Garment, Shopper

_overlay: ContextVar[DemoPayload | None] = ContextVar(
    "worthwearing_catalog_overlay", default=None
)


@lru_cache
def load_closet() -> list[Garment]:
    raw = json.loads((DATA_DIR / "closet.json").read_text(encoding="utf-8"))
    return [Garment.model_validate(item) for item in raw]


@lru_cache
def load_candidates() -> list[CandidateProduct]:
    raw = json.loads((DATA_DIR / "products.json").read_text(encoding="utf-8"))
    return [CandidateProduct.model_validate(item) for item in raw]


@lru_cache
def load_seed_demo() -> DemoPayload:
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


def load_demo() -> DemoPayload:
    overlay = _overlay.get()
    if overlay is not None:
        return overlay
    return load_seed_demo()


def get_candidate(candidate_id: str) -> CandidateProduct:
    for item in load_demo().candidates:
        if item.id == candidate_id:
            return item
    raise KeyError(candidate_id)


def closet_fingerprint(closet: list[Garment] | None = None) -> str:
    items = closet if closet is not None else load_demo().closet
    return ",".join(sorted(item.id for item in items))


def overlay_catalog(
    extra_closet: list[Garment] | None = None,
    extra_candidates: list[CandidateProduct] | None = None,
) -> Token[DemoPayload | None] | None:
    extras_c = extra_closet or []
    extras_p = extra_candidates or []
    if not extras_c and not extras_p:
        return None
    seed = load_seed_demo()
    payload = seed.model_copy(
        update={
            "closet": [*seed.closet, *extras_c],
            "candidates": [*seed.candidates, *extras_p],
        }
    )
    return _overlay.set(payload)


def reset_catalog_overlay(token: Token[DemoPayload | None] | None) -> None:
    if token is not None:
        _overlay.reset(token)


@contextmanager
def catalog_overlay(
    extra_closet: list[Garment] | None = None,
    extra_candidates: list[CandidateProduct] | None = None,
) -> Iterator[None]:
    token = overlay_catalog(extra_closet, extra_candidates)
    try:
        yield
    finally:
        reset_catalog_overlay(token)


def resolve_asset_path(image_url: str) -> Path | None:
    if not image_url:
        return None
    if image_url.startswith("http://") or image_url.startswith("https://"):
        return None
    raw = Path(image_url)
    if raw.is_file():
        return raw
    name = image_url.rsplit("/", 1)[-1]
    folders = [
        DATA_DIR / "assets",
        DATA_DIR.parent.parent / "frontend" / "public" / "assets",
        *upload_search_dirs(),
    ]
    env = os.environ.get("WORTHWEARING_UPLOAD_DIR")
    if env:
        folders.append(Path(env))
    seen: set[Path] = set()
    for folder in folders:
        resolved = folder.resolve() if folder.exists() else folder
        if resolved in seen:
            continue
        seen.add(resolved)
        path = folder / name
        if path.is_file():
            return path
    return None
