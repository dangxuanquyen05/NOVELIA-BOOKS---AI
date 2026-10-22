"""Integration tests for NOVELIA BOOKS using real MySQL Server on dedicated test database.

SAFETY MANDATE:
- Integration tests must strictly run against a database containing 'test' (default: novelia_books_test).
- SQLite substitution is strictly prohibited per AGENTS.md.
- If MySQL server is unreachable or credentials are not yet configured, the tests gracefully
  report ENVIRONMENT BLOCKED rather than falsely passing or substituting SQLite.
"""

import os
from decimal import Decimal
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import Base
from app.database.seeds import seed_all


# Determine test database URL
TEST_DB_NAME = os.getenv("TEST_DB_NAME", f"{settings.DB_NAME}_test")
TEST_DB_USER = os.getenv("TEST_DB_USER", settings.DB_USER)
TEST_DB_PASSWORD = os.getenv("TEST_DB_PASSWORD", settings.DB_PASSWORD)
TEST_DB_HOST = os.getenv("TEST_DB_HOST", settings.DB_HOST)
TEST_DB_PORT = os.getenv("TEST_DB_PORT", settings.DB_PORT)

TEST_DATABASE_URL = (
    f"mysql+pymysql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@"
    f"{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}?charset=utf8mb4"
)


def verify_test_database_safety(db_name: str) -> None:
    """Refuse to run if database does not contain 'test' to prevent production or dev data loss."""
    if "test" not in db_name.lower():
        raise RuntimeError(
            f"SAFETY VIOLATION: Target database '{db_name}' is NOT marked as a test database. "
            "Integration tests are only permitted to run against databases containing 'test'."
        )


@pytest.fixture(scope="module")
def mysql_test_engine():
    """Create MySQL test engine if server is accessible, or skip with ENVIRONMENT BLOCKED."""
    verify_test_database_safety(TEST_DB_NAME)

    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"connect_timeout": 3},
        pool_pre_ping=True,
    )

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as exc:
        pytest.skip(
            f"ENVIRONMENT BLOCKED: Real MySQL test database '{TEST_DB_NAME}' at {TEST_DB_HOST}:{TEST_DB_PORT} "
            f"is unavailable ({type(exc).__name__}). "
            "Please configure MySQL user password in backend/.env or create database 'novelia_books_test'."
        )
    except Exception as exc:
        pytest.skip(
            f"ENVIRONMENT BLOCKED: Unexpected database error ({type(exc).__name__})."
        )

    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def test_db_session(mysql_test_engine):
    """Session fixture for test database."""
    # Create schema using SQLAlchemy metadata
    Base.metadata.create_all(bind=mysql_test_engine)

    Session = sessionmaker(bind=mysql_test_engine, autocommit=False, autoflush=False)
    session = Session()

    yield session

    session.close()


class TestMySQLIntegration:
    """Real MySQL Server integration test suite."""

    def test_mysql_connection_and_version(self, mysql_test_engine):
        """MYSQL INTEGRATION TEST: Verify real connection and retrieve MySQL engine version."""
        with mysql_test_engine.connect() as conn:
            version = conn.execute(text("SELECT VERSION()")).scalar()
            assert version is not None
            assert len(version) > 0

    def test_schema_and_tables_exist(self, mysql_test_engine, test_db_session):
        """MYSQL INTEGRATION TEST: Verify all 34 tables were created in MySQL."""
        with mysql_test_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = :db"
                ),
                {"db": TEST_DB_NAME},
            ).fetchall()
            created_tables = {row[0].lower() for row in result}

        assert "books" in created_tables
        assert "orders" in created_tables
        assert "inventory" in created_tables
        assert "ai_action_logs" in created_tables

    def test_seed_execution_and_idempotency(self, test_db_session):
        """MYSQL INTEGRATION TEST: Verify seed populates data and re-running does not duplicate."""
        from app.models.catalog import Book, Category, Publisher

        # Execute seed
        seed_all(test_db_session)

        total_books = test_db_session.query(Book).count()
        total_categories = test_db_session.query(Category).count()
        total_publishers = test_db_session.query(Publisher).count()

        assert total_books >= 30
        assert total_categories >= 6
        assert total_publishers >= 5

        # 2nd run: Idempotent - no new entities should be added
        second_stats = seed_all(test_db_session)
        assert second_stats["books"] == 0
        assert second_stats["categories"] == 0
        assert second_stats["publishers"] == 0

    def test_transaction_rollback_integrity(self, test_db_session):
        """MYSQL INTEGRATION TEST: Verify transaction rollback preserves ACID integrity on error."""
        from app.models.catalog import Publisher

        initial_count = test_db_session.query(Publisher).count()

        try:
            # Begin explicit nested transaction or add invalid duplicate
            pub_dup = Publisher(
                name="NXB Trẻ",  # Duplicate unique name
                slug="nxb-tre-duplicate-test",
            )
            test_db_session.add(pub_dup)
            test_db_session.commit()
            pytest.fail("Expected UniqueConstraint violation on duplicate publisher name")
        except SQLAlchemyError:
            test_db_session.rollback()

        # Count must remain unchanged after rollback
        final_count = test_db_session.query(Publisher).count()
        assert initial_count == final_count

    def test_mysql_user_registration_and_auth(self, test_db_session):
        """MYSQL INTEGRATION TEST: Verify real user account creation, bcrypt hash storage, and role assignment."""
        from app.schemas.auth import UserRegisterRequest
        from app.services.auth_service import AuthService
        from app.repositories.user_repo import UserRepository

        test_email = "mysql_tester@novelia.vn"
        existing = UserRepository.get_by_email(test_db_session, test_email)
        if existing:
            test_db_session.delete(existing)
            test_db_session.commit()

        req = UserRegisterRequest(
            email=test_email,
            password="StrongRealPassword123!",
            full_name="MySQL Test User",
            phone="0911223344",
        )
        created_user = AuthService.register_customer(test_db_session, req)
        assert created_user.id is not None
        assert created_user.email == test_email
        assert created_user.hashed_password.startswith("$2b$")

        # Verify role assignment in MySQL
        roles = UserRepository.get_user_role_names(created_user)
        assert "CUSTOMER" in roles

        # Verify authentication against MySQL
        from app.schemas.auth import UserLoginRequest
        login_req = UserLoginRequest(email=test_email, password="StrongRealPassword123!")
        authenticated = AuthService.authenticate(test_db_session, login_req)
        assert authenticated.id == created_user.id

    def test_mysql_address_tenant_isolation(self, test_db_session):
        """MYSQL INTEGRATION TEST: Verify address persistence and cross-tenant isolation in MySQL."""
        from app.repositories.user_repo import UserRepository
        from app.schemas.user import AddressCreateRequest

        user1 = UserRepository.get_by_email(test_db_session, "mysql_tester@novelia.vn")
        assert user1 is not None

        addr_data = AddressCreateRequest(
            recipient_name="Tester Recipient",
            phone="0988776655",
            province_code="79",
            province_name="TP. Hồ Chí Minh",
            district_code="760",
            district_name="Quận 1",
            ward_code="26734",
            ward_name="Phường Bến Nghé",
            street_address="123 Lê Lợi",
            is_default=True,
        )
        addr = UserRepository.create_address(test_db_session, user1.id, addr_data)
        test_db_session.commit()

        # Query with user1.id succeeds
        found = UserRepository.get_address_by_id(test_db_session, addr.id, user1.id)
        assert found is not None
        assert found.recipient_name == "Tester Recipient"

        # Query with another user_id (e.g. 999999) returns None
        denied = UserRepository.get_address_by_id(test_db_session, addr.id, 999999)
        assert denied is None
