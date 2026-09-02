from app.models import Recommendation
from app.scoring import (
    RISK_WEIGHTS,
    ScoreInputs,
    analyze,
    factor_sum_reconciles,
    recommendation_for_risk,
)
from app.store import load_demo


def _run(candidate_id: str):
    demo = load_demo()
    candidate = next(item for item in demo.candidates if item.id == candidate_id)
    return analyze(
        ScoreInputs(
            candidate=candidate,
            closet=demo.closet,
            climate_tags=demo.shopper.climate_tags,
            target_occasions=demo.config.target_occasions,
            wear_horizon_months=demo.config.wear_horizon_months,
        )
    )


def test_jacket_a_is_skip_in_target_band():
    result = _run("jacket-a")
    assert result.recommendation == Recommendation.SKIP_IT
    assert 75 <= result.return_risk <= 90
    assert factor_sum_reconciles(result)


def test_jacket_b_is_worth_it_in_target_band():
    result = _run("jacket-b")
    assert result.recommendation == Recommendation.WORTH_IT
    assert 15 <= result.return_risk <= 35
    assert result.outfit_count >= 4
    assert factor_sum_reconciles(result)


def test_risk_weights_sum_to_one():
    assert abs(sum(RISK_WEIGHTS.values()) - 1.0) < 1e-9


def test_components_match_displayed_score():
    for candidate_id in ("jacket-a", "jacket-b"):
        result = _run(candidate_id)
        weighted = sum(factor.contribution for factor in result.factors)
        assert int(round(100 * weighted)) == result.return_risk
        assert result.worth_score == 100 - result.return_risk


def test_thresholds():
    assert recommendation_for_risk(0) == Recommendation.WORTH_IT
    assert recommendation_for_risk(39) == Recommendation.WORTH_IT
    assert recommendation_for_risk(40) == Recommendation.THINK_AGAIN
    assert recommendation_for_risk(69) == Recommendation.THINK_AGAIN
    assert recommendation_for_risk(70) == Recommendation.SKIP_IT
    assert recommendation_for_risk(100) == Recommendation.SKIP_IT


def test_jacket_a_duplicates_leather_jacket():
    result = _run("jacket-a")
    duplication = next(factor for factor in result.factors if factor.key == "duplication")
    assert duplication.value >= 0.8
    names = [item.name for item in result.matched_items]
    assert any("Leather" in name or "Biker" in name for name in names)
