"""User-uploaded wardrobe items and custom garment candidates."""

from __future__ import annotations

import os
from pathlib import Path

from app.config import DATA_DIR
from app.models import CandidateProduct, Garment

KIND_TAXONOMY: dict[str, dict[str, str]] = {
    "shirt": {"category": "tops", "subcategory": "shirt", "layer": "base"},
    "t-shirt": {"category": "tops", "subcategory": "tee", "layer": "base"},
    "sweater": {"category": "tops", "subcategory": "sweater", "layer": "mid"},
    "jacket": {"category": "outerwear", "subcategory": "jacket", "layer": "outer"},
    "coat": {"category": "outerwear", "subcategory": "coat", "layer": "outer"},
    "blazer": {"category": "outerwear", "subcategory": "blazer", "layer": "outer"},
    "pants": {"category": "bottoms", "subcategory": "pants", "layer": "bottom"},
    "jeans": {"category": "bottoms", "subcategory": "jeans", "layer": "bottom"},
    "skirt": {"category": "bottoms", "subcategory": "skirt", "layer": "bottom"},
    "shoes": {"category": "shoes", "subcategory": "shoes", "layer": "shoes"},
}

KIND_OPTIONS = list(KIND_TAXONOMY.keys())
COLOR_OPTIONS = [
    "black",
    "white",
    "navy",
    "blue",
    "gray",
    "charcoal",
    "brown",
    "beige",
    "olive",
    "cream",
    "ivory",
    "burgundy",
    "camel",
    "red",
    "indigo",
]
STYLE_OPTIONS = [
    "classic",
    "tailored",
    "casual",
    "workwear",
    "street",
    "edgy",
    "minimal",
    "versatile",
]
SEASON_OPTIONS = ["fall", "winter", "spring", "summer"]
OCCASION_OPTIONS = ["work", "weekend", "commute", "evening"]

ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024


def taxonomy_for_kind(kind: str) -> dict[str, str]:
    key = kind.strip().lower()
    if key not in KIND_TAXONOMY:
        raise ValueError(f"Unknown garment type: {kind}")
    return KIND_TAXONOMY[key]


def garment_category_for(item: Garment) -> str:
    """Perfect Corp cloth-v4 garment_category for a scored item."""
    if item.layer == "outer" or item.category == "outerwear":
        return "outer"
    if item.layer == "bottom" or item.category == "bottoms":
        return "lower"
    if item.layer == "shoes" or item.category == "shoes":
        return "lower"
    if item.subcategory == "dress" or item.category == "dresses":
        return "full_body"
    return "upper"


def upload_search_dirs() -> list[Path]:
    folders = [DATA_DIR / "uploads", Path("/tmp/worthwearing-uploads")]
    env = os.environ.get("WORTHWEARING_UPLOAD_DIR")
    if env:
        folders.insert(0, Path(env))
    return folders


def writable_upload_dir() -> Path:
    last_error: OSError | None = None
    for folder in upload_search_dirs():
        try:
            folder.mkdir(parents=True, exist_ok=True)
            probe = folder / ".write-ok"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return folder
        except OSError as exc:
            last_error = exc
    raise RuntimeError("No writable upload directory.") from last_error


def save_upload(data: bytes, original_name: str, prefix: str) -> str:
    if not data:
        raise ValueError("Photo is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("Photo must be 8 MB or smaller.")
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        suffix = ".jpg"
    dest_name = f"{prefix}{suffix}"
    dest = writable_upload_dir() / dest_name
    dest.write_bytes(data)
    return dest_name


def make_custom_closet_item(
    *,
    item_id: str,
    name: str,
    kind: str,
    colors: list[str],
    styles: list[str],
    seasons: list[str],
    occasions: list[str],
    price: float | None,
    filename: str,
) -> Garment:
    tax = taxonomy_for_kind(kind)
    return Garment(
        id=item_id,
        name=name.strip(),
        category=tax["category"],
        subcategory=tax["subcategory"],
        colors=colors,
        style_tags=styles,
        season_tags=seasons,
        occasion_tags=occasions,
        layer=tax["layer"],
        image_url=f"/assets/{filename}",
        price=price if price else None,
        description="Uploaded to this session’s wardrobe.",
        brand=None,
    )


def make_custom_candidate(
    *,
    item_id: str,
    name: str,
    kind: str,
    colors: list[str],
    styles: list[str],
    seasons: list[str],
    occasions: list[str],
    price: float | None,
    filename: str,
) -> CandidateProduct:
    tax = taxonomy_for_kind(kind)
    label = name.strip()[:24] or "Yours"
    image_url = f"/assets/{filename}"
    return CandidateProduct(
        id=item_id,
        name=name.strip(),
        short_label=label,
        demo_role="custom",
        category=tax["category"],
        subcategory=tax["subcategory"],
        colors=colors,
        style_tags=styles,
        season_tags=seasons,
        occasion_tags=occasions,
        layer=tax["layer"],
        image_url=image_url,
        price=price if price else None,
        description="Uploaded garment scored against the current wardrobe.",
        brand=None,
        prepared_try_on_url=image_url,
        prepared_try_on_alt=(
            f"Uploaded photo of {name.strip()}. Used when live try-on is unavailable."
        ),
        scenario_assets=[],
    )
