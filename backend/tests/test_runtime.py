from app.models import Recommendation
from app.runtime import analyze_candidate, asset_path, try_on_mode


def test_runtime_scores_both_jackets():
    a = analyze_candidate("jacket-a")
    b = analyze_candidate("jacket-b")
    assert a.recommendation == Recommendation.SKIP_IT
    assert b.recommendation == Recommendation.WORTH_IT
    assert 75 <= a.return_risk <= 90
    assert 15 <= b.return_risk <= 35


def test_asset_path_finds_shopper():
    path = asset_path("/assets/shopper-portrait.png")
    assert path is not None and path.is_file()


def test_try_on_mode_is_demo_in_unit_tests():
    assert try_on_mode().value == "demo"
