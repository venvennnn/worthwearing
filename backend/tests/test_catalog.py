from app.catalog import (
    garment_category_for,
    make_custom_candidate,
    make_custom_closet_item,
    save_upload,
)
from app.config import DATA_DIR
from app.outfits import OutfitEngine
from app.runtime import analyze_candidate, asset_path
from app.store import catalog_overlay, get_candidate, load_demo, resolve_asset_path


def _white_shirt(*, item_id: str, as_candidate: bool):
    kwargs = dict(
        item_id=item_id,
        name="White Oxford Shirt",
        kind="shirt",
        colors=["white"],
        styles=["classic", "tailored", "workwear"],
        seasons=["fall", "winter", "spring"],
        occasions=["work", "weekend", "commute"],
        price=80,
        filename="closet-white-oxford.png",
    )
    if as_candidate:
        return make_custom_candidate(**kwargs)
    return make_custom_closet_item(**kwargs)


def test_custom_shirt_is_scored_against_closet():
    candidate = _white_shirt(item_id="custom-shirt-1", as_candidate=True)
    result = analyze_candidate("custom-shirt-1", extra_candidates=[candidate])
    assert result.candidate_id == "custom-shirt-1"
    assert result.return_risk == int(round(100 * sum(factor.contribution for factor in result.factors)))
    duplication = next(factor for factor in result.factors if factor.key == "duplication")
    assert duplication.value >= 0.9
    assert "White Oxford Shirt" in duplication.explanation
    assert result.outfit_count >= 1
    assert any(piece.layer == "bottom" for outfit in result.outfits for piece in outfit.pieces)


def test_extra_closet_item_is_included_in_scoring():
    extra = make_custom_closet_item(
        item_id="user-closet-olive-tee",
        name="Olive Weekend Tee",
        kind="t-shirt",
        colors=["olive"],
        styles=["casual"],
        seasons=["fall", "spring"],
        occasions=["weekend"],
        price=40,
        filename="closet-gray-tee.png",
    )
    baseline = analyze_candidate("jacket-a")
    updated = analyze_candidate("jacket-a", extra_closet=[extra])
    assert baseline.factors[1].explanation != updated.factors[1].explanation


def test_overlay_resolves_custom_candidate():
    candidate = _white_shirt(item_id="custom-shirt-2", as_candidate=True)
    with catalog_overlay(extra_candidates=[candidate]):
        found = get_candidate("custom-shirt-2")
        demo = load_demo()
        assert found.name == "White Oxford Shirt"
        assert any(item.id == "custom-shirt-2" for item in demo.candidates)
        assert len(demo.closet) == 12
    # Overlay must not leak after the context exits.
    try:
        get_candidate("custom-shirt-2")
        raised = False
    except KeyError:
        raised = True
    assert raised


def test_save_upload_and_asset_path(tmp_path, monkeypatch):
    monkeypatch.setenv("WORTHWEARING_UPLOAD_DIR", str(tmp_path))
    data = (DATA_DIR / "assets" / "closet-white-oxford.png").read_bytes()
    filename = save_upload(data, "shirt.png", "user-item-abc")
    assert filename == "user-item-abc.png"
    path = asset_path(f"/assets/{filename}")
    assert path is not None and path.is_file()
    assert resolve_asset_path(f"/assets/{filename}") == path


def test_garment_category_maps_shirts_to_upper():
    candidate = _white_shirt(item_id="custom-shirt-3", as_candidate=True)
    assert garment_category_for(candidate) == "upper"
    jacket = load_demo().candidates[0]
    assert garment_category_for(jacket) == "outer"


def test_shirt_outfits_use_bottoms_not_other_shirts():
    demo = load_demo()
    shirt = next(item for item in demo.closet if item.id == "closet-white-oxford")
    outfits, _ = OutfitEngine().build_outfits(shirt, [item for item in demo.closet if item.id != shirt.id])
    assert outfits
    for outfit in outfits:
        layers = [piece.layer for piece in outfit.pieces]
        assert "bottom" in layers
        assert layers.count("base") == 1
