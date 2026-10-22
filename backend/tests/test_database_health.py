"""Tests for database health endpoint covering success, failure, and security."""

from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_database_health_success_mocked():
    """Verify that GET /api/v1/health/database returns 200 when database check succeeds."""
    mock_success = (
        True,
        "Database query executed successfully",
        {
            "database": "novelia_books",
            "host": "127.0.0.1",
            "port": 3306,
            "status": "connected",
        },
    )
    with patch("app.api.v1.health.check_database_connection", return_value=mock_success):
        response = client.get("/api/v1/health/database")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "novelia_books"
        assert "executed successfully" in data["message"]
        assert data["details"]["status"] == "connected"


def test_database_health_failure_mocked_no_secret_leak():
    """Verify that GET /api/v1/health/database returns 503 on error without exposing credentials."""
    mock_failure = (
        False,
        "Unable to connect to MySQL database server",
        {
            "database": "novelia_books",
            "host": "127.0.0.1",
            "port": 3306,
            "status": "disconnected",
            "error_type": "OperationalError",
        },
    )
    with patch("app.api.v1.health.check_database_connection", return_value=mock_failure):
        response = client.get("/api/v1/health/database")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "novelia_books"
        assert "Unable to connect" in data["message"]

        # Critical Security Assertion: Zero credential or sensitive info leakage
        raw_text = response.text.lower()
        assert "password" not in raw_text
        assert "mysql+pymysql" not in raw_text
        assert "root:" not in raw_text
        assert "traceback" not in raw_text


def test_database_health_live_endpoint():
    """Live endpoint probe: returns either 200 (if MySQL configured) or 503 (if DB offline).
    
    In either case, ensures structured response and zero secret leakage.
    """
    response = client.get("/api/v1/health/database")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "unhealthy"]
    assert "database" in data
    # Ensure no credentials in live output
    assert "password" not in response.text.lower()
