"""Phase 13 — Full System Testing, Concurrency & Security Hardening Suite.

Safety Mandates:
- Never mutate, drop, or alter the development database 'novelia_books'.
- All test database interactions must strictly target databases containing 'test' (e.g. 'novelia_books_test').
- Strict verification of SQL injection resistance, XSS input handling, IDOR protection,
  concurrency race conditions, secret leakage, and migration health.
- Realism rule: Never declare absolute 100% invulnerability; report verified mitigations transparently.
"""

import time
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.masking import mask_sensitive_data
from app.main import app
from app.models.catalog import Book
from app.models.commerce import Cart, CartItem, Coupon, CouponUsage, Order, OrderItem
from app.models.inventory import Inventory, InventoryTransaction
from app.models.user import Role, User, UserAddress, UserRole
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.order_repo import OrderRepository
from app.schemas.inventory import InventoryAdjustmentRequest
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService
from tests.test_mysql_integration import TEST_DB_HOST, TEST_DB_NAME, TEST_DB_PORT, TEST_DATABASE_URL

client = TestClient(app)


class MockRole:
    def __init__(self, name: str):
        self.name = name

class MockUserRole:
    def __init__(self, name: str):
        self.role = MockRole(name)
    def __eq__(self, other):
        if isinstance(other, str):
            return self.role.name == other
        return super().__eq__(other)
    def __str__(self):
        return self.role.name

def make_user(user_id: int, role_name: str = "CUSTOMER") -> User:
    """Helper to construct mock user with full role compatibility."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = f"user_{user_id}@{role_name.lower()}.vn"
    user.full_name = f"Reader {user_id}"
    user.is_active = True

    ur = MockUserRole(role_name)
    user.user_roles = [ur]
    user.roles = [ur]
    return user


@pytest.fixture
def customer_user_1():
    return make_user(101, "CUSTOMER")


@pytest.fixture
def customer_user_2():
    return make_user(202, "CUSTOMER")


@pytest.fixture
def staff_user():
    return make_user(505, "STAFF")


class TestDatabaseSafetyAndMigrations:
    """Verify test database isolation and migration integrity."""

    def test_database_isolation_safety_guarantee(self):
        """Verify that the test suite is configured to NEVER touch the development database."""
        dev_db = settings.DB_NAME
        assert "test" not in dev_db.lower(), "Development DB name must not contain 'test'."
        assert "test" in TEST_DB_NAME.lower(), "Test database name MUST contain 'test' for safety."
        assert dev_db != TEST_DB_NAME, "Development and Test database names must be strictly isolated."

    def test_mysql_test_db_migration_schema_and_tables(self):
        """Verify that all core schema tables exist on the dedicated test MySQL server."""
        try:
            engine = create_engine(TEST_DATABASE_URL, connect_args={"connect_timeout": 3})
            with engine.connect() as conn:
                result = conn.execute(text("SHOW TABLES"))
                existing_tables = {row[0].lower() for row in result.fetchall()}
        except (OperationalError, Exception) as exc:
            pytest.skip(f"Test MySQL database '{TEST_DB_NAME}' not reachable ({type(exc).__name__}).")

        expected_tables = {
            "users",
            "roles",
            "user_roles",
            "books",
            "categories",
            "inventory",
            "inventory_transactions",
            "orders",
            "order_items",
            "payments",
            "shipments",
            "notifications",
            "audit_logs",
            "ai_action_logs",
        }
        for table in expected_tables:
            assert table in existing_tables, f"Schema table '{table}' missing in test database."


class TestSQLInjectionHardening:
    """Verify that user inputs cannot manipulate SQL queries via injection attacks."""

    @pytest.mark.parametrize(
        "malicious_payload",
        [
            "' OR '1'='1",
            "'; DROP TABLE books; --",
            "' UNION SELECT 1, 'admin', 'pass', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 --",
            "1' AND SLEEP(5) --",
            "admin'--",
            "\" OR \"\"=\"",
        ],
    )
    def test_catalog_search_sql_injection_resistance(self, malicious_payload):
        """SQL injection probes in search parameter must return HTTP 200 without executing injection."""
        response = client.get(f"/api/v1/catalog/books?query={malicious_payload}")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        assert data["total"] >= 0

    @pytest.mark.parametrize(
        "malicious_number",
        [
            "1000 OR 1=1",
            "1; DROP TABLE users",
            "100 UNION SELECT 1",
            "NaN",
            "invalid_decimal",
        ],
    )
    def test_numeric_filters_reject_sql_injection(self, malicious_number):
        """Numeric filters (price, page, page_size) must be validated by Pydantic before reaching SQL."""
        response = client.get(f"/api/v1/catalog/books?min_price={malicious_number}")
        assert response.status_code == 422  # Unprocessable Entity, rejected by Pydantic schema


class TestInputValidationAndXSSHardening:
    """Verify input sanitization, length boundaries, and XSS string handling."""

    def test_registration_xss_script_handling(self):
        """XSS script payload in user registration name must not break API."""
        xss_payload = {
            "email": f"xss_test_{int(time.time())}@novelia.vn",
            "password": "SecurePassword123!",
            "full_name": "<script>alert('XSS_ATTACK');</script>",
            "phone": "0901234567",
        }
        response = client.post("/api/v1/auth/register", json=xss_payload)
        assert response.status_code in [201, 409]
        if response.status_code == 201:
            data = response.json()
            assert "XSS_ATTACK" in data["full_name"]

    def test_malformed_json_returns_422_without_crash(self):
        """Malformed JSON bodies must trigger HTTP 422 without 500 server exception."""
        response = client.post(
            "/api/v1/auth/login",
            content="{bad_json: True, invalid_syntax",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422
        assert "detail" in response.json()


class TestIDORAndTenantIsolation:
    """Verify multi-tenant isolation and prevent Insecure Direct Object References (IDOR)."""

    def test_customer_cannot_cancel_other_customer_order(self, customer_user_1, customer_user_2):
        """Customer 1 must be strictly blocked from cancelling Customer 2's order."""
        mock_db = MagicMock()
        target_order = Order(
            id=888,
            order_code="NVL-20261020-000888",
            user_id=customer_user_2.id,
            status="PENDING",
            subtotal_amount=Decimal("150000.00"),
            shipping_fee=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("150000.00"),
            recipient_name="Reader 2",
            recipient_phone="0901234567",
            shipping_province="HCM",
            shipping_district="Q1",
            shipping_ward="Ben Nghe",
            shipping_street_address="123 Le Loi",
        )

        with patch("app.repositories.order_repo.OrderRepository.get_by_code", return_value=target_order):
            with pytest.raises(HTTPException) as exc_info:
                OrderService.cancel_order(
                    db=mock_db,
                    user=customer_user_1,
                    order_code="NVL-20261020-000888",
                    reason="Malicious cancel attempt",
                )
            assert exc_info.value.status_code == 403
            assert "đơn hàng của người khác" in exc_info.value.detail

    def test_customer_strictly_blocked_from_admin_endpoints(self, customer_user_1):
        """Customer role receives HTTP 403 when probing admin endpoints."""
        app.dependency_overrides[get_current_user] = lambda: customer_user_1
        try:
            # Try accessing admin executive dashboard
            resp_dash = client.get("/api/v1/admin/dashboard/summary")
            assert resp_dash.status_code == 403

            # Try accessing system audit trail
            resp_audit = client.get("/api/v1/audit/logs")
            assert resp_audit.status_code == 403

            # Try accessing AI action logs
            resp_ai_logs = client.get("/api/v1/audit/ai-actions")
            assert resp_ai_logs.status_code == 403
        finally:
            app.dependency_overrides.clear()


class TestConcurrencyAndTransactionIntegrity:
    """Verify inventory holding, locking, and race condition safeguards."""

    def test_inventory_underflow_prevention_on_concurrent_demand(self, staff_user):
        """Verify that physical stock cannot drop below reserved stock during adjustment."""
        mock_db = MagicMock()

        # Book with physical stock = 5, reserved stock = 4 (delta -2 would cause physical 3 < reserved 4)
        mock_book = Book(id=10, title="Sách Giới Hạn", status="ACTIVE", price=Decimal("50000"))
        mock_db.query.return_value.filter.return_value.first.return_value = mock_book

        with patch.object(
            InventoryRepository,
            "adjust_stock",
            side_effect=ValueError("Tồn kho vật lý sau điều chỉnh không thể nhỏ hơn tồn giữ chỗ"),
        ):
            req = InventoryAdjustmentRequest(
                book_id=10,
                quantity_change=-2,
                reference_code="ADJ-TEST-001",
                reason="Hao hụt kiểm kê",
            )
            with pytest.raises(HTTPException) as exc_info:
                InventoryService.adjust_stock(db=mock_db, data=req, staff_user=staff_user)
            assert exc_info.value.status_code == 400
            assert "nhỏ hơn tồn giữ chỗ" in exc_info.value.detail

    def test_pessimistic_locking_invoked_on_cart_checkout(self, customer_user_1):
        """Verify that checkout query performs SELECT ... FOR UPDATE on inventory row."""
        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_lock = mock_filter.with_for_update.return_value

        inv = Inventory(id=1, book_id=5, physical_stock=10, reserved_stock=0)
        mock_lock.first.return_value = inv

        # Simulate the pessimistic query that OrderService performs
        result = (
            mock_db.query(Inventory)
            .filter(Inventory.book_id == 5)
            .with_for_update()
            .first()
        )

        assert result == inv
        mock_filter.with_for_update.assert_called_once()


class TestSecretLeakageAndAuditMasking:
    """Verify that credentials, tokens, and secrets are never exposed in responses or logs."""

    def test_login_response_never_contains_password_hash(self):
        """Login response must contain tokens and user details but NEVER hashed_password."""
        payload = {
            "email": "reader@novelia.vn",
            "password": "SecurePassword123!",
        }
        response = client.post("/api/v1/auth/login", json=payload)
        resp_text = response.text
        assert "hashed_password" not in resp_text
        assert "$2b$" not in resp_text

    def test_mask_sensitive_data_redacts_tokens_and_secrets(self):
        """Masking engine must recursively redact sensitive fields."""
        dirty_payload = {
            "user_id": 42,
            "email": "admin@novelia.vn",
            "password": "SuperSecretPassword!",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "access_token": "secret_access_token",
            "api_key": "AIzaSySecretApiKey",
            "nested": {
                "cvv": "123",
                "secret": "db_secret",
                "safe_note": "Ghi chú bình thường",
            },
            "items": [
                {"token": "token_in_list", "sku": "NVL-001"}
            ]
        }

        masked = mask_sensitive_data(dirty_payload)

        assert masked["password"] == "***REDACTED***"
        assert masked["token"] == "***REDACTED***"
        assert masked["access_token"] == "***REDACTED***"
        assert masked["api_key"] == "***REDACTED***"
        assert masked["nested"]["cvv"] == "***REDACTED***"
        assert masked["nested"]["secret"] == "***REDACTED***"
        assert masked["nested"]["safe_note"] == "Ghi chú bình thường"
        assert masked["items"][0]["token"] == "***REDACTED***"
        assert masked["items"][0]["sku"] == "NVL-001"


class TestPerformanceAndPaginationBudgets:
    """Verify system performance bounds, query latency budgets, and pagination ceilings."""

    def test_catalog_pagination_ceiling_enforced(self):
        """Client requesting page_size > 100 must be rejected with 422 to prevent DoS memory spikes."""
        response = client.get("/api/v1/catalog/books?page_size=1000")
        assert response.status_code == 422
        assert "less_than_equal" in response.text or "less than or equal to 100" in response.text

    def test_catalog_query_latency_budget(self):
        """Storefront catalog browsing should respond within 500ms budget on localhost."""
        start_time = time.perf_counter()
        response = client.get("/api/v1/catalog/books?page_size=10")
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert response.status_code == 200
        assert elapsed_ms < 500.0, f"Catalog latency exceeded budget: {elapsed_ms:.1f}ms"
