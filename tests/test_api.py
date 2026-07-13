"""Tests for FastAPI application."""
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_pipeline_validation():
    response = client.post("/api/v1/pipeline/run", json={"gene_symbol": ""})
    assert response.status_code == 422  # validation error on empty gene


def test_screening_validation():
    response = client.post("/api/v1/screening/run", json={"gene_symbol": ""})
    assert response.status_code == 422


def test_docking_endpoint_exists():
    """Docking endpoint should be registered and accept requests."""
    # The endpoint may fail with 500 if external tools (obabel, vina) are missing,
    # but the route itself should be registered and reachable.
    try:
        response = client.post("/api/v1/docking/run", json={})
        assert response.status_code in (200, 500)
    except FileNotFoundError:
        # Expected if obabel/vina are not installed on this machine
        pass


def test_job_not_found():
    response = client.get("/api/v1/job/nonexistent")
    assert response.status_code == 404
