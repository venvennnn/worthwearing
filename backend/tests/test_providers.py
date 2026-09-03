from app.catalog import garment_category_for, make_custom_candidate
from app.models import ProviderMode, TryOnJob, TryOnStatus
from app.providers.perfect_corp import PerfectCorpProvider


def test_normalize_success_status():
    provider = PerfectCorpProvider()
    job = TryOnJob(
        job_id="live-1",
        status=TryOnStatus.PROCESSING,
        provider=ProviderMode.LIVE,
    )
    body = {
        "status": 200,
        "data": {
            "error": None,
            "results": {"url": "https://example.com/result.png"},
            "task_status": "success",
        },
    }
    updated = provider._normalize_status(body, job)
    assert updated.status == TryOnStatus.COMPLETED
    assert updated.result_image_url == "https://example.com/result.png"


def test_normalize_error_status():
    provider = PerfectCorpProvider()
    job = TryOnJob(
        job_id="live-1",
        status=TryOnStatus.PROCESSING,
        provider=ProviderMode.LIVE,
    )
    body = {
        "data": {
            "error": "error_pose",
            "task_status": "error",
        }
    }
    updated = provider._normalize_status(body, job)
    assert updated.status == TryOnStatus.FAILED
    assert updated.error_category == "provider_error"


def test_normalize_create_task_id():
    provider = PerfectCorpProvider()
    task_id = provider._normalize_create({"status": 200, "data": {"task_id": "abc"}})
    assert task_id == "abc"


def test_payload_uses_official_fields():
    provider = PerfectCorpProvider()
    payload = provider._task_payload("src-1", "ref-1")
    assert payload["src_file_id"] == "src-1"
    assert payload["ref_file_id"] == "ref-1"
    assert payload["garment_category"] == "outer"
    assert "Authorization" not in payload


def test_payload_shirt_uses_upper_category():
    provider = PerfectCorpProvider()
    shirt = make_custom_candidate(
        item_id="custom-shirt-cat",
        name="White Oxford Shirt",
        kind="shirt",
        colors=["white"],
        styles=["classic"],
        seasons=["fall"],
        occasions=["work"],
        price=80,
        filename="closet-white-oxford.png",
    )
    payload = provider._task_payload("src-1", "ref-1", garment_category_for(shirt))
    assert payload["garment_category"] == "upper"


def test_asset_path_resolves_demo_files():
    provider = PerfectCorpProvider()
    path = provider._asset_path("/assets/shopper-portrait.png")
    assert path.is_file()
