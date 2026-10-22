"""Unit tests for basic application health endpoint."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify that the root endpoint returns API service information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "NOVELIA BOOKS API"
    assert "version" in data
    assert data["health_check"] == "/api/v1/health"
    assert data["database_health"] == "/api/v1/health/database"


def test_app_health_endpoint():
    """Verify that GET /api/v1/health returns healthy without depending on MySQL."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "novelia-books-backend"
    assert data["version"] == "1.0.0"
    assert "environment" in data
    assert "timestamp" in data


def test_cors_headers_on_health_endpoint():
    """Regression test: Verify that CORS headers are properly returned for allowed origin."""
    response = client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_preflight_options_request():
    """Regression test: Verify that OPTIONS preflight request succeeds with CORS headers."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
