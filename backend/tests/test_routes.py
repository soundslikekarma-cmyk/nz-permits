"""Tests for route checking."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_routes():
    r = client.get("/routes")
    assert r.status_code == 200
    routes = r.json()
    assert len(routes) >= 5
    assert any(route["id"] == "tauranga_auckland" for route in routes)


def test_check_route_cat_4b_house_finds_issues():
    payload = {
        "route_id": "tauranga_auckland",
        "width_m": 6.5,
        "height_m": 5.2,
        "length_m": 14.0,
        "weight_kg": 28000,
    }
    r = client.post("/check-route", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["route_id"] == "tauranga_auckland"
    assert data["summary"]["total"] >= 2
    # Should hit the height-related and Cat 4B issues
    assert any("Kaimai" in i["title"] or "Auckland" in i["title"] for i in data["issues"])


def test_check_route_standard_load_few_issues():
    payload = {
        "route_id": "tauranga_auckland",
        "width_m": 2.5,
        "height_m": 4.0,
        "length_m": 20.0,
        "weight_kg": 40000,
    }
    r = client.post("/check-route", json=payload)
    assert r.status_code == 200
    data = r.json()
    # Should trigger toll road notice but not the major restrictions
    assert data["summary"]["blockers"] == 0


def test_check_route_blocker_for_wide_load_on_motorway():
    payload = {
        "route_id": "tauranga_auckland",
        "width_m": 6.0,
        "height_m": 4.0,
        "length_m": 14.0,
        "weight_kg": 28000,
    }
    r = client.post("/check-route", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["summary"]["blockers"] >= 1
    assert not data["summary"]["clear_to_proceed"]


def test_unknown_route_returns_404():
    payload = {
        "route_id": "nonexistent_route",
        "width_m": 2.5,
        "height_m": 4.0,
        "length_m": 20.0,
        "weight_kg": 40000,
    }
    r = client.post("/check-route", json=payload)
    assert r.status_code == 404
