from pydantic import ValidationError

import pytest

from app.models import Garment
from app.scoring import ScoreInputs, analyze
from app.store import load_demo


def test_malformed_garment_rejected():
    with pytest.raises(ValidationError):
        Garment.model_validate(
            {
                "id": "x",
                "name": "Broken",
                "category": "tops",
                "subcategory": "shirt",
                "colors": "black",
                "style_tags": [],
                "season_tags": [],
                "occasion_tags": [],
                "layer": "base",
                "image_url": "/x.png",
            }
        )


def test_unknown_candidate_not_in_demo_payload():
    demo = load_demo()
    ids = {item.id for item in demo.candidates}
    assert "jacket-c" not in ids


def test_empty_closet_still_returns_scores():
    demo = load_demo()
    candidate = demo.candidates[0]
    result = analyze(
        ScoreInputs(
            candidate=candidate,
            closet=[],
            climate_tags=demo.shopper.climate_tags,
            target_occasions=demo.config.target_occasions,
        )
    )
    assert 0 <= result.return_risk <= 100
    assert result.outfit_count == 0
