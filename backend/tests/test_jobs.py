"""Tests for job storage endpoints."""
import os
import tempfile
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, tmp_path):
    """Use a temp SQLite file for each test, so tests don't share state."""
    from app import database
    test_db = tmp_path / "test_jobs.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    database.init_db()
    yield


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


SAMPLE_DEVICE = "test-device-12345678"


def _sample_payload(name: str = "Test job"):
    return {
        "device_id": SAMPLE_DEVICE,
        "name": name,
        "load_input": {"width_m": 6.5, "height_m": 5.2, "length_m": 14.0, "weight_kg": 28000, "indivisible": True},
        "classification": {"category": "cat_4b", "category_label": "Category 4B"},
        "route_check": None,
    }


def test_save_job(client):
    r = client.post("/jobs", json=_sample_payload())
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Test job"
    assert data["device_id"] == SAMPLE_DEVICE
    assert data["id"]  # has an ID
    assert data["created_at"]
    assert data["route_check"] is None


def test_list_jobs_empty_for_new_device(client):
    r = client.get("/jobs", params={"device_id": "unused-device-99999"})
    assert r.status_code == 200
    assert r.json() == []


def test_list_jobs_returns_newest_first(client):
    client.post("/jobs", json=_sample_payload("Job 1"))
    client.post("/jobs", json=_sample_payload("Job 2"))
    client.post("/jobs", json=_sample_payload("Job 3"))
    r = client.get("/jobs", params={"device_id": SAMPLE_DEVICE})
    assert r.status_code == 200
    jobs = r.json()
    assert len(jobs) == 3
    assert jobs[0]["name"] == "Job 3"
    assert jobs[2]["name"] == "Job 1"


def test_get_job_by_id(client):
    create_response = client.post("/jobs", json=_sample_payload("Specific job"))
    job_id = create_response.json()["id"]
    r = client.get(f"/jobs/{job_id}")
    assert r.status_code == 200
    assert r.json()["name"] == "Specific job"


def test_get_nonexistent_job_returns_404(client):
    r = client.get("/jobs/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_delete_job(client):
    create_response = client.post("/jobs", json=_sample_payload())
    job_id = create_response.json()["id"]
    r = client.delete(f"/jobs/{job_id}", params={"device_id": SAMPLE_DEVICE})
    assert r.status_code == 200
    assert r.json()["deleted"] is True
    # Confirm it's gone
    r2 = client.get(f"/jobs/{job_id}")
    assert r2.status_code == 404


def test_delete_job_wrong_device(client):
    create_response = client.post("/jobs", json=_sample_payload())
    job_id = create_response.json()["id"]
    r = client.delete(f"/jobs/{job_id}", params={"device_id": "wrong-device-12345"})
    assert r.status_code == 404
    # Confirm the job still exists with the correct device
    r2 = client.get(f"/jobs/{job_id}")
    assert r2.status_code == 200


def test_jobs_isolated_by_device(client):
    """Two devices' jobs don't leak across."""
    client.post("/jobs", json={**_sample_payload("Device A job"), "device_id": "device-aaaaa12345"})
    client.post("/jobs", json={**_sample_payload("Device B job"), "device_id": "device-bbbbb67890"})
    r_a = client.get("/jobs", params={"device_id": "device-aaaaa12345"})
    r_b = client.get("/jobs", params={"device_id": "device-bbbbb67890"})
    assert len(r_a.json()) == 1
    assert len(r_b.json()) == 1
    assert r_a.json()[0]["name"] == "Device A job"
    assert r_b.json()[0]["name"] == "Device B job"
