"""Database engine, session management, and health verification utilities."""

import logging
from typing import Any, Dict, Generator, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import settings

logger = logging.getLogger("novelia.database")

# Create SQLAlchemy engine with connection pooling, pre-ping validation, and fast timeout
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"connect_timeout": 5},
    echo=(settings.ENVIRONMENT == "development_verbose"),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency injection yield for transactional database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> Tuple[bool, str, Dict[str, Any]]:
    """Execute real 'SELECT 1' query against MySQL to verify live database health.
    
    Returns:
        Tuple of (is_healthy, status_message, details_dict).
        Guarantees zero leakage of credentials, passwords, or raw connection strings.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            if result == 1:
                return (
                    True,
                    "Database query executed successfully",
                    {
                        "database": settings.DB_NAME,
                        "host": settings.DB_HOST,
                        "port": settings.DB_PORT,
                        "status": "connected",
                    },
                )
            return (
                False,
                "Unexpected query result from database",
                {"database": settings.DB_NAME, "status": "unhealthy"},
            )
    except SQLAlchemyError as exc:
        # Sanitize and log generic error without exposing credentials
        logger.error("Database health check failed: %s", type(exc).__name__)
        return (
            False,
            "Unable to connect to MySQL database server",
            {
                "database": settings.DB_NAME,
                "host": settings.DB_HOST,
                "port": settings.DB_PORT,
                "status": "disconnected",
                "error_type": type(exc).__name__,
            },
        )
    except Exception as exc:
        logger.error("Unexpected error during database health check: %s", type(exc).__name__)
        return (
            False,
            "Database service is currently unavailable",
            {"database": settings.DB_NAME, "status": "error"},
        )
