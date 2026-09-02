from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["mcp_active"] is False


def test_demo_payload_has_twelve_closet_items_and_two_jackets():
    response = client.get("/api/demo")
    assert response.status_code == 200
    body = response.json()
    assert len(body["closet"]) == 12
    assert {item["id"] for item in body["candidates"]} == {"jacket-a", "jacket-b"}
    assert "api_key" not in str(body).lower()


def test_analyze_jacket_a_and_b():
    a = client.post("/api/analyze", json={"candidate_id": "jacket-a"}).json()
    b = client.post("/api/analyze", json={"candidate_id": "jacket-b"}).json()
    assert a["recommendation"] == "skip_it"
    assert b["recommendation"] == "worth_it"
    assert a["return_risk"] > b["return_risk"]


def test_try_on_demo_completes():
    import time

    created = client.post(
        "/api/try-on", json={"candidate_id": "jacket-b", "shopper_asset_id": "shopper-maya"}
    )
    assert created.status_code == 200
    job_id = created.json()["job_id"]
    status = None
    for _ in range(12):
        status = client.get(f"/api/try-on/{job_id}").json()
        if status["status"] == "completed":
            break
        time.sleep(0.2)
    assert status["status"] == "completed"
    assert status["result_image_url"]
    assert status["provider"] == "demo"


def test_unknown_candidate():
    response = client.post("/api/analyze", json={"candidate_id": "nope"})
    assert response.status_code == 404
