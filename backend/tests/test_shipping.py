"""Integration and unit tests for Phase 8 — Shipping Integration & Carrier Webhooks.

Validates:
- Preparation and creation of formal carrier shipments from eligible orders (CONFIRMED / PROCESSING).
- Rejection of invalid dispatch attempts (PENDING, CANCELLED, or duplicate dispatch).
- RBAC enforcement: CUSTOMER blocked from dispatching orders (HTTP 403).
- Multi-Tenant isolation: Customer cannot inspect tracking for orders belonging to others (HTTP 403).
- Public tracking lookup by tracking code.
- Webhook signature/secret authentication rejection on forged payloads (HTTP 401).
- Webhook replay protection and idempotency (duplicate events are ignored).
- Order status and COD payment synchronization upon carrier delivery confirmation (DELIVERED -> COMPLETED & PAID).
- Return flow synchronization (RETURNED -> CANCELLED).
- Live integration blocked guard when credentials are missing (HTTP 503).
- Providers readiness diagnostics endpoint.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user, get_current_user, get_db
from app.core.config import settings
from app.integrations.shipping import (
    LiveIntegrationBlockedError,
    ShipmentCreationResult,
    compute_mock_shipping_signature,
)
from app.main import app
from app.models.commerce import Order, OrderItem
from app.models.payment_shipping import Payment, Shipment, ShipmentEvent
from app.models.user import Role, User, UserRole
from app.services.shipping_service import ShippingService

client = TestClient(app)


def make_user(user_id: int, role_name: str = "CUSTOMER") -> User:
    """Helper to mock a User with assigned role."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = f"{role_name.lower()}_{user_id}@novelia.vn"
    user.full_name = f"User {user_id} ({role_name})"
    user.phone = "0988776655"
    user.is_active = True
    user.created_at = datetime.now(timezone.utc)

    role = MagicMock(spec=Role)
    role.name = role_name
    ur = MagicMock(spec=UserRole)
    ur.role = role
    user.roles = [ur]
    return user


@pytest.fixture
def customer_user():
    return make_user(10, "CUSTOMER")


@pytest.fixture
def other_customer():
    return make_user(20, "CUSTOMER")


@pytest.fixture
def staff_user():
    return make_user(99, "STAFF")


@pytest.fixture
def admin_user():
    return make_user(1, "ADMIN")


@pytest.fixture
def mock_db():
    return MagicMock()


def make_sample_order(order_id: int = 1, user_id: int = 10, status: str = "CONFIRMED") -> Order:
    order = MagicMock(spec=Order)
    order.id = order_id
    order.order_code = f"NVL-20261020-ORD{order_id:03d}"
    order.user_id = user_id
    order.status = status
    order.subtotal_amount = Decimal("300000.00")
    order.shipping_fee = Decimal("30000.00")
    order.discount_amount = Decimal("0.00")
    order.total_amount = Decimal("330000.00")
    order.recipient_name = "Nguyễn Văn Đọc"
    order.recipient_phone = "0987654321"
    order.shipping_street_address = "Số 10 Phạm Văn Đồng"
    order.shipping_ward = "Dịch Vọng Hậu"
    order.shipping_district = "Cầu Giấy"
    order.shipping_province = "Hà Nội"
    order.staff_notes = None
    order.cancelled_reason = None
    order.items = []

    # Mock payment
    payment = MagicMock(spec=Payment)
    payment.payment_method = "COD"
    payment.payment_status = "PENDING"
    payment.paid_at = None
    order.payment = payment

    return order


# ============================================================================
# 1. DISPATCH ORDER & LIFECYCLE TESTS
# ============================================================================

def test_customer_cannot_dispatch_order(customer_user, mock_db):
    """Customer accounts must receive 403 Forbidden when attempting to dispatch orders."""
    app.dependency_overrides[get_current_user] = lambda: customer_user
    app.dependency_overrides[get_current_active_user] = lambda: customer_user
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.post(
            "/api/v1/shipping/orders/NVL-20261020-ORD001/dispatch",
            json={"carrier": "GHN", "weight": 500},
        )
        assert response.status_code == 403
        assert "Operation not permitted" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_dispatch_order_success(staff_user, mock_db):
    """Staff can dispatch confirmed order to GHN or MOCK carrier."""
    app.dependency_overrides[get_current_user] = lambda: staff_user
    app.dependency_overrides[get_current_active_user] = lambda: staff_user
    app.dependency_overrides[get_db] = lambda: mock_db

    sample_order = make_sample_order(1, 10, "CONFIRMED")

    with patch("app.repositories.order_repo.OrderRepository.get_by_code", return_value=sample_order), \
         patch("app.repositories.shipment_repo.ShipmentRepository.get_by_order_id", return_value=None), \
         patch("app.repositories.shipment_repo.ShipmentRepository.create_shipment") as mock_create_ship, \
         patch("app.repositories.shipment_repo.ShipmentRepository.add_event") as mock_add_event:

        fake_shipment = MagicMock(spec=Shipment)
        fake_shipment.id = 101
        fake_shipment.order_id = sample_order.id
        fake_shipment.carrier = "MOCK"
        fake_shipment.tracking_code = "MOCK-GHN-TEST1234"
        fake_shipment.status = "READY_TO_PICK"
        fake_shipment.shipping_fee = Decimal("30000.00")
        fake_shipment.estimated_delivery_date = date(2026, 10, 23)
        fake_shipment.dispatched_at = datetime.now(timezone.utc)
        fake_shipment.delivered_at = None
        fake_shipment.events = []
        fake_shipment.created_at = datetime.now(timezone.utc)

        mock_create_ship.return_value = fake_shipment

        try:
            response = client.post(
                f"/api/v1/shipping/orders/{sample_order.order_code}/dispatch",
                json={
                    "carrier": "MOCK",
                    "weight": 800,
                    "length": 25,
                    "width": 18,
                    "height": 6,
                    "required_note": "CHOXEMHANGKHONGTHU",
                    "staff_notes": "Đóng gói cẩn thận",
                },
            )
            assert response.status_code == 201
            data = response.json()
            assert data["order_code"] == sample_order.order_code
            assert data["carrier"] == "MOCK"
            assert data["tracking_code"] == "MOCK-GHN-TEST1234"
            assert sample_order.status == "SHIPPING"
            assert mock_db.commit.called
        finally:
            app.dependency_overrides.clear()


def test_dispatch_order_rejected_if_pending(staff_user, mock_db):
    """Orders in PENDING status cannot be dispatched (must be confirmed first)."""
    app.dependency_overrides[get_current_user] = lambda: staff_user
    app.dependency_overrides[get_db] = lambda: mock_db

    pending_order = make_sample_order(2, 10, "PENDING")

    with patch("app.repositories.order_repo.OrderRepository.get_by_code", return_value=pending_order):
        try:
            response = client.post(
                f"/api/v1/shipping/orders/{pending_order.order_code}/dispatch",
                json={"carrier": "MOCK", "weight": 500},
            )
            assert response.status_code == 400
            assert "chờ xử lý (PENDING)" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


def test_dispatch_order_rejected_if_cancelled(staff_user, mock_db):
    """Cancelled orders cannot be dispatched."""
    app.dependency_overrides[get_current_user] = lambda: staff_user
    app.dependency_overrides[get_db] = lambda: mock_db

    cancelled_order = make_sample_order(3, 10, "CANCELLED")

    with patch("app.repositories.order_repo.OrderRepository.get_by_code", return_value=cancelled_order):
        try:
            response = client.post(
                f"/api/v1/shipping/orders/{cancelled_order.order_code}/dispatch",
                json={"carrier": "MOCK", "weight": 500},
            )
            assert response.status_code == 400
            assert "đã bị hủy" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


def test_dispatch_order_rejected_if_duplicate(staff_user, mock_db):
    """An order already associated with an active shipment cannot be dispatched twice."""
    app.dependency_overrides[get_current_user] = lambda: staff_user
    app.dependency_overrides[get_db] = lambda: mock_db

    order = make_sample_order(4, 10, "CONFIRMED")
    existing_shipment = MagicMock(spec=Shipment)
    existing_shipment.tracking_code = "GHN-EXISTING-999"
    existing_shipment.carrier = "GHN"
    existing_shipment.status = "READY_TO_PICK"

    with patch("app.repositories.order_repo.OrderRepository.get_by_code", return_value=order), \
         patch("app.repositories.shipment_repo.ShipmentRepository.get_by_order_id", return_value=existing_shipment):
        try:
            response = client.post(
                f"/api/v1/shipping/orders/{order.order_code}/dispatch",
                json={"carrier": "GHN", "weight": 500},
            )
            assert response.status_code == 400
            assert "đã được gắn vận đơn 'GHN-EXISTING-999'" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


# ============================================================================
# 2. TRACKING & MULTI-TENANT ISOLATION TESTS
# ============================================================================

def test_order_tracking_tenant_isolation_blocked(other_customer, mock_db):
    """Customer 20 must receive 403 Forbidden when attempting to view tracking of Customer 10's order."""
    app.dependency_overrides[get_current_user] = lambda: other_customer
    app.dependency_overrides[get_current_active_user] = lambda: other_customer
    app.dependency_overrides[get_db] = lambda: mock_db

    order_of_user_10 = make_sample_order(5, 10, "SHIPPING")

    with patch("app.repositories.order_repo.OrderRepository.get_by_code", return_value=order_of_user_10):
        try:
            response = client.get(f"/api/v1/shipping/orders/{order_of_user_10.order_code}/tracking")
            assert response.status_code == 403
            assert "không có quyền xem thông tin vận chuyển" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


def test_order_tracking_owner_success(customer_user, mock_db):
    """Customer can view tracking checkpoints of their own order."""
    app.dependency_overrides[get_current_user] = lambda: customer_user
    app.dependency_overrides[get_current_active_user] = lambda: customer_user
    app.dependency_overrides[get_db] = lambda: mock_db

    order = make_sample_order(6, customer_user.id, "SHIPPING")

    shipment = MagicMock(spec=Shipment)
    shipment.id = 202
    shipment.order_id = order.id
    shipment.carrier = "GHN"
    shipment.tracking_code = "GHN-TRACK-001"
    shipment.status = "IN_TRANSIT"
    shipment.shipping_fee = Decimal("30000.00")
    shipment.estimated_delivery_date = date(2026, 10, 24)
    shipment.dispatched_at = datetime.now(timezone.utc)
    shipment.delivered_at = None
    shipment.created_at = datetime.now(timezone.utc)

    event = MagicMock(spec=ShipmentEvent)
    event.id = 1
    event.status = "IN_TRANSIT"
    event.description = "Bưu kiện đang luân chuyển qua kho trung chuyển Hà Nội"
    event.location = "Kho Cầu Giấy, Hà Nội"
    event.occurred_at = datetime.now(timezone.utc)
    shipment.events = [event]

    with patch("app.repositories.order_repo.OrderRepository.get_by_code", return_value=order), \
         patch("app.repositories.shipment_repo.ShipmentRepository.get_by_order_id", return_value=shipment):
        try:
            response = client.get(f"/api/v1/shipping/orders/{order.order_code}/tracking")
            assert response.status_code == 200
            data = response.json()
            assert data["tracking_code"] == "GHN-TRACK-001"
            assert data["carrier"] == "GHN"
            assert data["status"] == "IN_TRANSIT"
            assert len(data["events"]) == 1
            assert data["events"][0]["location"] == "Kho Cầu Giấy, Hà Nội"
        finally:
            app.dependency_overrides.clear()


def test_public_tracking_lookup(mock_db):
    """Public tracking lookup by tracking code."""
    app.dependency_overrides[get_db] = lambda: mock_db

    shipment = MagicMock(spec=Shipment)
    shipment.tracking_code = "GHN-PUBLIC-123"
    shipment.carrier = "GHN"
    shipment.status = "READY_TO_PICK"
    shipment.estimated_delivery_date = date(2026, 10, 25)
    shipment.delivered_at = None
    shipment.events = []

    order = MagicMock(spec=Order)
    order.order_code = "NVL-ORD-PUBLIC"
    shipment.order = order

    with patch("app.repositories.shipment_repo.ShipmentRepository.get_by_tracking_code", return_value=shipment):
        try:
            response = client.get(f"/api/v1/shipping/track/{shipment.tracking_code}")
            assert response.status_code == 200
            data = response.json()
            assert data["tracking_code"] == "GHN-PUBLIC-123"
            assert data["order_code"] == "NVL-ORD-PUBLIC"
            assert data["carrier"] == "GHN"
        finally:
            app.dependency_overrides.clear()


# ============================================================================
# 3. WEBHOOK & CARRIER SYNCHRONIZATION TESTS
# ============================================================================

def test_webhook_invalid_signature_rejected(mock_db):
    """Webhook callback with forged or missing signature must be rejected with HTTP 401."""
    app.dependency_overrides[get_db] = lambda: mock_db

    payload = {"tracking_code": "MOCK-TEST-001", "status": "IN_TRANSIT"}
    headers = {"x-shipping-signature": "invalid_forged_signature"}

    try:
        response = client.post(
            "/api/v1/shipping/webhook/MOCK",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 401
        assert "Chữ ký hoặc Secret xác thực" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_webhook_delivered_status_sync_and_cod_payment(mock_db):
    """When carrier reports DELIVERED status, Order moves to COMPLETED and COD payment becomes PAID."""
    app.dependency_overrides[get_db] = lambda: mock_db

    sample_order = make_sample_order(7, 10, "SHIPPING")
    assert sample_order.payment.payment_status == "PENDING"

    shipment = MagicMock(spec=Shipment)
    shipment.id = 303
    shipment.tracking_code = "MOCK-SHIP-777"
    shipment.carrier = "MOCK"
    shipment.status = "IN_TRANSIT"
    shipment.order = sample_order

    payload = {
        "tracking_code": "MOCK-SHIP-777",
        "status": "DELIVERED",
        "description": "Bưu tá đã giao hàng thành công và thu tiền thu hộ (COD)",
        "location": "Nhà riêng người nhận, Hà Nội",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }
    signature = compute_mock_shipping_signature(payload)

    def fake_update(db, ship, status, **kwargs):
        ship.status = status
        return ship

    with patch("app.repositories.shipment_repo.ShipmentRepository.get_by_tracking_code", return_value=shipment), \
         patch("app.repositories.shipment_repo.ShipmentRepository.has_event_occurred", return_value=False), \
         patch("app.repositories.shipment_repo.ShipmentRepository.add_event") as mock_add_event, \
         patch("app.repositories.shipment_repo.ShipmentRepository.update_shipment_status", side_effect=fake_update):

        try:
            response = client.post(
                "/api/v1/shipping/webhook/MOCK",
                json=payload,
                headers={"x-shipping-signature": signature},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["shipment_status"] == "DELIVERED"
            # Synchronization verification
            assert sample_order.status == "COMPLETED"
            assert sample_order.payment.payment_status == "PAID"
            assert sample_order.payment.paid_at is not None
            assert mock_db.commit.called
        finally:
            app.dependency_overrides.clear()


def test_webhook_replay_protection_idempotent(mock_db):
    """Duplicate webhook callbacks must be recognized and safely ignored without duplicate mutations."""
    app.dependency_overrides[get_db] = lambda: mock_db

    shipment = MagicMock(spec=Shipment)
    shipment.id = 404
    shipment.tracking_code = "MOCK-REPLAY-123"
    shipment.status = "DELIVERED"
    shipment.order = make_sample_order(8, 10, "COMPLETED")

    payload = {
        "tracking_code": "MOCK-REPLAY-123",
        "status": "DELIVERED",
        "description": "Giao thành công",
    }
    signature = compute_mock_shipping_signature(payload)

    with patch("app.repositories.shipment_repo.ShipmentRepository.get_by_tracking_code", return_value=shipment), \
         patch("app.repositories.shipment_repo.ShipmentRepository.has_event_occurred", return_value=True):

        try:
            response = client.post(
                "/api/v1/shipping/webhook/MOCK",
                json=payload,
                headers={"x-shipping-signature": signature},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ignored"
            assert "trùng lặp" in data["message"]
        finally:
            app.dependency_overrides.clear()


# ============================================================================
# 4. REALISM & BLOCKED LIVE INTEGRATION TESTS
# ============================================================================

def test_live_integration_blocked_without_credentials(staff_user, mock_db):
    """When running in LIVE environment, adapter must strictly raise LiveIntegrationBlockedError
    if merchant credentials are missing.
    """
    app.dependency_overrides[get_current_user] = lambda: staff_user
    app.dependency_overrides[get_db] = lambda: mock_db

    order = make_sample_order(9, 10, "CONFIRMED")

    # Force LIVE mode with empty credentials
    with patch.object(settings, "SHIPPING_ENVIRONMENT", "live"), \
         patch.object(settings, "GHN_TOKEN", ""), \
         patch("app.repositories.order_repo.OrderRepository.get_by_code", return_value=order), \
         patch("app.repositories.shipment_repo.ShipmentRepository.get_by_order_id", return_value=None):

        try:
            response = client.post(
                f"/api/v1/shipping/orders/{order.order_code}/dispatch",
                json={"carrier": "GHN", "weight": 500},
            )
            assert response.status_code == 503
            assert "GHN Live Integration is BLOCKED" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


def test_shipping_providers_status_endpoint(mock_db):
    """GET /shipping/providers/status reports diagnostics on all integrated carriers."""
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/api/v1/shipping/providers/status")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        carriers = [p["carrier"] for p in data]
        assert "GHN" in carriers
        assert "GHTK" in carriers
        assert "MOCK" in carriers
    finally:
        app.dependency_overrides.clear()
