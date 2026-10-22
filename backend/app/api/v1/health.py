"""Health check and diagnostics API endpoints."""

from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.database.connection import check_database_connection

router = APIRouter()


class HealthResponse(BaseModel):
    """Schema for basic application health check."""

    status: str = Field(..., examples=["healthy"])
    service: str = Field(..., examples=["novelia-books-backend"])
    version: str = Field(..., examples=["1.0.0"])
    environment: str = Field(..., examples=["development"])
    timestamp: str = Field(...)


class DatabaseHealthResponse(BaseModel):
    """Schema for database connectivity health check."""

    status: str = Field(..., examples=["healthy"])
    database: str = Field(..., examples=["novelia_books"])
    message: str = Field(...)
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(...)


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Application Health Check",
    description="Verify that the FastAPI application is running. Does not depend on MySQL.",
)
def get_app_health() -> HealthResponse:
    """Check backend application liveness."""
    return HealthResponse(
        status="healthy",
        service="novelia-books-backend",
        version="1.0.0",
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/health/database",
    response_model=DatabaseHealthResponse,
    responses={
        status.HTTP_200_OK: {"description": "MySQL database connection healthy"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "MySQL database connection failed"},
    },
    summary="Database Connectivity Health Check",
    description="Executes a real 'SELECT 1' query against MySQL Server to confirm live connectivity.",
)
def get_database_health(response: Response) -> DatabaseHealthResponse:
    """Verify live connectivity and query execution against MySQL Server."""
    is_healthy, message, details = check_database_connection()

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return DatabaseHealthResponse(
            status="unhealthy",
            database=settings.DB_NAME,
            message=message,
            details=details,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    response.status_code = status.HTTP_200_OK
    return DatabaseHealthResponse(
        status="healthy",
        database=settings.DB_NAME,
        message=message,
        details=details,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
