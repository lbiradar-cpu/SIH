import io
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    # TestClient as a context manager triggers FastAPI startup/shutdown
    # events (init_db creates tables + seeds rules).
    with TestClient(app) as c:
        yield c


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_inspect_rejects_bad_file_type(client):
    fake_file = io.BytesIO(b"not an image")
    response = client.post(
        "/api/inspect",
        files={"image": ("test.txt", fake_file, "text/plain")},
    )
    assert response.status_code == 400


def test_inspect_accepts_jpeg_and_returns_result(client):
    fake_jpeg = io.BytesIO(b"\xff\xd8\xff\xe0fake-jpeg-bytes")
    response = client.post(
        "/api/inspect",
        files={"image": ("test.jpg", fake_jpeg, "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert "id" in body
    assert body["status"] in ("COMPLIANT", "NON_COMPLIANT")
    assert "declarations" in body
    assert "violations" in body


def test_rules_endpoint(client):
    response = client.get("/api/rules")
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_dashboard_endpoint(client):
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    assert "total_inspections" in response.json()
