from app.outfits import OutfitEngine
from app.store import load_demo


def test_jacket_b_unlocks_at_least_four_outfits():
    demo = load_demo()
    candidate = next(item for item in demo.candidates if item.id == "jacket-b")
    outfits, _ = OutfitEngine().build_outfits(candidate, demo.closet)
    assert len(outfits) >= 4
    ids = {outfit.id for outfit in outfits}
    assert len(ids) == len(outfits)


def test_rejected_combinations_have_rules():
    demo = load_demo()
    candidate = next(item for item in demo.candidates if item.id == "jacket-a")
    outfits, rejected = OutfitEngine().build_outfits(candidate, demo.closet)
    assert outfits
    assert rejected
    for row in rejected:
        assert row.rule in {"color", "style", "season", "occasion", "layer"}
        assert row.reason
