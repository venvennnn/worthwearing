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
    from app.models import TryOnRequest

    provider = PerfectCorpProvider()
    payload = provider._build_try_on_payload(
        TryOnRequest(candidate_id="jacket-a", shopper_asset_id="shopper-maya")
    )
    assert "src_file_url" in payload
    assert "ref_file_url" in payload
    assert "garment_category" in payload
    assert "Authorization" not in payload
