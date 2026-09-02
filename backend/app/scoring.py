"""Deterministic Return Risk / Worth Score calculations.

Every recommendation is produced from explicit formulas. An LLM, if present,
must receive this evidence as context and must never change the scores.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models import (
    AnalysisResult,
    CostPerWearScenario,
    FactorComponent,
    Garment,
    MatchedItem,
    Recommendation,
    RejectedCombination,
)
from app.outfits import OutfitEngine, jaccard

DUPLICATION_WEIGHTS = {
    "color": 0.20,
    "subcategory": 0.30,
    "style": 0.35,
    "season": 0.15,
}

RISK_WEIGHTS = {
    "duplication": 0.30,
    "style_isolation": 0.25,
    "climate_mismatch": 0.20,
    "occasion_narrowness": 0.15,
    "usage_uncertainty": 0.10,
}

COMPAT_WEIGHTS = {
    "style_isolation": 0.40,
    "climate_mismatch": 0.25,
    "occasion_narrowness": 0.20,
    "duplication": 0.15,
}

THRESHOLD_WORTH_IT = 39
THRESHOLD_THINK_AGAIN = 69


def weighted_item_similarity(candidate: Garment, other: Garment) -> float:
    color = jaccard(candidate.colors, other.colors)
    subcategory = 1.0 if candidate.subcategory == other.subcategory else 0.0
    style = jaccard(candidate.style_tags, other.style_tags)
    season = jaccard(candidate.season_tags, other.season_tags)
    return (
        DUPLICATION_WEIGHTS["color"] * color
        + DUPLICATION_WEIGHTS["subcategory"] * subcategory
        + DUPLICATION_WEIGHTS["style"] * style
        + DUPLICATION_WEIGHTS["season"] * season
    )


def duplication_score(candidate: Garment, closet: list[Garment]) -> tuple[float, Garment | None, float]:
    same_category = [
        item
        for item in closet
        if item.category == candidate.category and item.id != candidate.id
    ]
    if not same_category:
        return 0.0, None, 0.0
    best: Garment | None = None
    best_score = 0.0
    for item in same_category:
        score = weighted_item_similarity(candidate, item)
        if score > best_score:
            best_score = score
            best = item
    return best_score, best, best_score


def style_isolation_score(
    candidate: Garment, closet: list[Garment], engine: OutfitEngine
) -> tuple[float, int, int]:
    eligible = [
        item
        for item in closet
        if item.category != candidate.category and item.id != candidate.id
    ]
    if not eligible:
        return 1.0, 0, 0
    compatible = [
        item
        for item in eligible
        if engine.styles_compatible(candidate, item) and engine.colors_compatible(candidate, item)
    ]
    proportion = len(compatible) / len(eligible)
    return 1.0 - proportion, len(compatible), len(eligible)


def climate_mismatch_score(candidate: Garment, climate_tags: list[str]) -> float:
    if not candidate.season_tags or not climate_tags:
        return 0.5
    return 1.0 - jaccard(candidate.season_tags, climate_tags)


def occasion_narrowness_score(candidate: Garment, target_occasions: list[str]) -> tuple[float, int, int]:
    if not target_occasions:
        return 0.0, 0, 0
    supported = [occ for occ in candidate.occasion_tags if occ in target_occasions]
    return 1.0 - (len(supported) / len(target_occasions)), len(supported), len(target_occasions)


def usage_uncertainty_score(
    outfit_count: int,
    supported_occasions: int,
    target_occasion_count: int,
) -> float:
    if outfit_count <= 0:
        outfit_term = 1.0
    elif outfit_count == 1:
        outfit_term = 0.90
    elif outfit_count == 2:
        outfit_term = 0.70
    elif outfit_count == 3:
        outfit_term = 0.45
    else:
        outfit_term = max(0.05, 1.0 - (outfit_count / 10.0))

    if target_occasion_count <= 0:
        wear_term = 0.5
    else:
        wear_term = 1.0 - (supported_occasions / target_occasion_count)
    return min(1.0, 0.65 * outfit_term + 0.35 * wear_term)


def recommendation_for_risk(risk: int) -> Recommendation:
    if risk <= THRESHOLD_WORTH_IT:
        return Recommendation.WORTH_IT
    if risk <= THRESHOLD_THINK_AGAIN:
        return Recommendation.THINK_AGAIN
    return Recommendation.SKIP_IT


RECOMMENDATION_LABELS = {
    Recommendation.WORTH_IT: "Worth It",
    Recommendation.THINK_AGAIN: "Think Again",
    Recommendation.SKIP_IT: "Skip It",
}


def estimated_wears(
    outfit_count: int,
    occasion_coverage: float,
    horizon_months: int,
) -> int:
    """Scenario wears over a visible horizon. Not a prediction."""
    base = max(1, outfit_count) * 2
    coverage_boost = 1.0 + occasion_coverage
    horizon_factor = horizon_months / 12
    return max(2, round(base * coverage_boost * horizon_factor * 2.5))


@dataclass
class ScoreInputs:
    candidate: Garment
    closet: list[Garment]
    climate_tags: list[str]
    target_occasions: list[str]
    wear_horizon_months: int = 12


def analyze(inputs: ScoreInputs) -> AnalysisResult:
    engine = OutfitEngine()
    outfits, rejected = engine.build_outfits(inputs.candidate, inputs.closet)

    d_value, twin, twin_similarity = duplication_score(inputs.candidate, inputs.closet)
    i_value, compatible_count, eligible_count = style_isolation_score(
        inputs.candidate, inputs.closet, engine
    )
    c_value = climate_mismatch_score(inputs.candidate, inputs.climate_tags)
    o_value, supported_count, target_count = occasion_narrowness_score(
        inputs.candidate, inputs.target_occasions
    )
    u_value = usage_uncertainty_score(len(outfits), supported_count, target_count)

    risk_raw = (
        RISK_WEIGHTS["duplication"] * d_value
        + RISK_WEIGHTS["style_isolation"] * i_value
        + RISK_WEIGHTS["climate_mismatch"] * c_value
        + RISK_WEIGHTS["occasion_narrowness"] * o_value
        + RISK_WEIGHTS["usage_uncertainty"] * u_value
    )
    return_risk = int(round(100 * risk_raw))
    return_risk = max(0, min(100, return_risk))

    compat_raw = (
        COMPAT_WEIGHTS["style_isolation"] * i_value
        + COMPAT_WEIGHTS["climate_mismatch"] * c_value
        + COMPAT_WEIGHTS["occasion_narrowness"] * o_value
        + COMPAT_WEIGHTS["duplication"] * d_value
    )
    wardrobe_compatibility = int(round(100 - 100 * compat_raw))
    wardrobe_compatibility = max(0, min(100, wardrobe_compatibility))
    worth_score = max(0, min(100, 100 - return_risk))

    rec = recommendation_for_risk(return_risk)

    factors = [
        FactorComponent(
            key="duplication",
            label="Duplication",
            value=round(d_value, 4),
            weight=RISK_WEIGHTS["duplication"],
            contribution=round(RISK_WEIGHTS["duplication"] * d_value, 4),
            explanation=(
                f"Closest same-category match is {twin.name} "
                f"(weighted Jaccard {twin_similarity:.2f})."
                if twin
                else "No same-category closet item, so duplication is zero."
            ),
        ),
        FactorComponent(
            key="style_isolation",
            label="Style isolation",
            value=round(i_value, 4),
            weight=RISK_WEIGHTS["style_isolation"],
            contribution=round(RISK_WEIGHTS["style_isolation"] * i_value, 4),
            explanation=(
                f"{compatible_count} of {eligible_count} eligible closet items "
                "share compatible style and color with this garment."
            ),
        ),
        FactorComponent(
            key="climate_mismatch",
            label="Climate mismatch",
            value=round(c_value, 4),
            weight=RISK_WEIGHTS["climate_mismatch"],
            contribution=round(RISK_WEIGHTS["climate_mismatch"] * c_value, 4),
            explanation=(
                "Season tags "
                f"{', '.join(inputs.candidate.season_tags) or 'none'} versus climate "
                f"{', '.join(inputs.climate_tags) or 'none'} "
                f"(Jaccard mismatch {c_value:.2f})."
            ),
        ),
        FactorComponent(
            key="occasion_narrowness",
            label="Occasion narrowness",
            value=round(o_value, 4),
            weight=RISK_WEIGHTS["occasion_narrowness"],
            contribution=round(RISK_WEIGHTS["occasion_narrowness"] * o_value, 4),
            explanation=(
                f"Supports {supported_count} of {target_count} target occasions "
                f"({', '.join(inputs.target_occasions)})."
            ),
        ),
        FactorComponent(
            key="usage_uncertainty",
            label="Usage uncertainty",
            value=round(u_value, 4),
            weight=RISK_WEIGHTS["usage_uncertainty"],
            contribution=round(RISK_WEIGHTS["usage_uncertainty"] * u_value, 4),
            explanation=(
                f"{len(outfits)} compatible outfits and "
                f"{supported_count}/{target_count} occasion coverage. "
                "Uncertainty rises when outfits are few or wear assumptions are weak."
            ),
        ),
    ]

    matched: list[MatchedItem] = []
    if twin:
        matched.append(
            MatchedItem(
                item_id=twin.id,
                name=twin.name,
                image_url=twin.image_url,
                reason="Highest weighted Jaccard similarity in the same category.",
                similarity=round(twin_similarity, 4),
            )
        )
    for outfit in outfits:
        for piece in outfit.pieces:
            if piece.item_id == inputs.candidate.id:
                continue
            if any(m.item_id == piece.item_id for m in matched):
                continue
            matched.append(
                MatchedItem(
                    item_id=piece.item_id,
                    name=piece.name,
                    image_url=piece.image_url,
                    reason=f"Appears in the {outfit.occasion} outfit.",
                )
            )

    cpw = None
    if inputs.candidate.price is not None:
        coverage = supported_count / target_count if target_count else 0.0
        wears = estimated_wears(len(outfits), coverage, inputs.wear_horizon_months)
        cpw = CostPerWearScenario(
            price=inputs.candidate.price,
            estimated_wears=wears,
            estimated_cpw=round(inputs.candidate.price / wears, 2),
            horizon_months=inputs.wear_horizon_months,
            formula="price / estimated_wears",
            assumptions=[
                f"{inputs.wear_horizon_months}-month wear horizon (visible demo assumption).",
                f"Estimated wears scale with {len(outfits)} compatible outfits and "
                f"{supported_count}/{target_count} occasion coverage.",
                "This is a scenario, not a predicted cost-per-wear.",
            ],
        )

    if rec == Recommendation.SKIP_IT:
        summary = (
            f"{inputs.candidate.name} visually works, but the wardrobe math says it "
            "is likely to sit unused: high duplication and a narrow wear pattern."
        )
    elif rec == Recommendation.THINK_AGAIN:
        summary = (
            f"{inputs.candidate.name} has mixed wardrobe evidence. Review the factors "
            "before treating this as a keep-worthy add."
        )
    else:
        summary = (
            f"{inputs.candidate.name} unlocks multiple outfits across the shopper’s "
            "climate and occasions, so the wardrobe case for keeping it is strong."
        )

    return AnalysisResult(
        candidate_id=inputs.candidate.id,
        candidate_name=inputs.candidate.name,
        recommendation=rec,
        recommendation_label=RECOMMENDATION_LABELS[rec],
        return_risk=return_risk,
        worth_score=worth_score,
        wardrobe_compatibility=wardrobe_compatibility,
        factors=factors,
        matched_items=matched,
        rejected_combinations=rejected,
        outfits=outfits,
        outfit_count=len(outfits),
        cost_per_wear=cpw,
        summary=summary,
        methodology_notes=[
            "WorthWearing is a decision-support prototype, not a calibrated return predictor.",
            "return_risk = round(100 × (0.30D + 0.25I + 0.20C + 0.15O + 0.10U)).",
            "Wardrobe compatibility = 100 − round(100 × (0.40I + 0.25C + 0.20O + 0.15D)).",
            "Worth Score = 100 − Return Risk.",
            "Worth It = 0–39, Think Again = 40–69, Skip It = 70–100.",
            "Cost per wear is an estimated scenario from outfit count, occasion coverage, "
            "and a twelve-month assumption.",
        ],
        is_prototype=True,
    )


def factor_sum_reconciles(result: AnalysisResult) -> bool:
    total = sum(factor.contribution for factor in result.factors)
    return int(round(100 * total)) == result.return_risk
