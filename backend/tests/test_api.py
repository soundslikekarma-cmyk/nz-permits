"""API-level tests using FastAPI's TestClient."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_classify_standard_load():
    payload = {
        "width_m": 2.5,
        "height_m": 4.0,
        "length_m": 20.0,
        "weight_kg": 40000,
        "indivisible": True,
    }
    response = client.post("/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "standard"
    assert data["requires_permit"] is False
    assert data["pilots"]["front_count"] == 0


def test_classify_cat_4b_house():
    payload = {
        "width_m": 6.5,
        "height_m": 5.2,
        "length_m": 14.0,
        "weight_kg": 28000,
        "indivisible": True,
    }
    response = client.post("/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "cat_4b"
    assert data["requires_permit"] is True
    assert data["requires_engineering_assessment"] is True
    assert data["pilots"]["front_count"] == 2
    assert data["pilots"]["rear_count"] == 1
    assert "engineer" in " ".join(data["notes"]).lower()


def test_classify_validation_rejects_zero_width():
    payload = {
        "width_m": 0,
        "height_m": 4.0,
        "length_m": 20.0,
        "weight_kg": 40000,
    }
    response = client.post("/classify", json=payload)
    assert response.status_code == 422  # Pydantic validation error


def test_classify_validation_rejects_huge_width():
    payload = {
        "width_m": 20,  # > 15m cap
        "height_m": 4.0,
        "length_m": 20.0,
        "weight_kg": 40000,
    }
    response = client.post("/classify", json=payload)
    assert response.status_code == 422


def test_permit_status_none_for_standard_load():
    payload = {"width_m": 2.5, "height_m": 4.0, "length_m": 20.0, "weight_kg": 40000}
    r = client.post("/classify", json=payload)
    assert r.json()["permit_status"] == "none"


def test_permit_status_overweight_only():
    payload = {"width_m": 2.5, "height_m": 4.0, "length_m": 20.0, "weight_kg": 60000}
    r = client.post("/classify", json=payload)
    assert r.json()["permit_status"] == "overweight"
    assert "overweight" in r.json()["permit_status_label"].lower()


def test_permit_status_overdimension_only():
    payload = {"width_m": 4.0, "height_m": 4.0, "length_m": 20.0, "weight_kg": 40000}
    r = client.post("/classify", json=payload)
    assert r.json()["permit_status"] == "overdimension"


def test_permit_status_both():
    payload = {"width_m": 4.0, "height_m": 4.0, "length_m": 20.0, "weight_kg": 60000}
    r = client.post("/classify", json=payload)
    assert r.json()["permit_status"] == "both"


def test_permit_status_cat_4b():
    payload = {"width_m": 6.5, "height_m": 5.2, "length_m": 14.0, "weight_kg": 28000}
    r = client.post("/classify", json=payload)
    assert r.json()["permit_status"] == "cat_4b"
