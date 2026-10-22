"""Integration and unit tests for Phase 6 — Checkout, Orders & Payment Abstraction."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.integrations.payment.mock import compute_mock_signature
from app.main import app
from app.models.catalog import Book
from app.models.commerce import Cart, CartItem, Coupon, CouponUsage, Order, OrderItem
from app.models.inventory import Inventory, InventoryTransaction
from app.models.payment_shipping import Payment
from app.models.user import Role, User, UserRole
from app.services.order_service import OrderService

client = TestClient(app)


@pytest.fixture
def mock_db():
    return MagicMock()


def make_user(user_id: int, role_name: str = "CUSTOMER") -> User:
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = f"user_{user_id}@{role_name.lower()}.vn"
    user.full_name = f"Reader {user_id}"
    user.is_active = True

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
def sample_book():
    book = Book(
        id=101,
        title="Nhà Giả Kim",
        isbn="978-604-00-1111-1",
        sku="NVL-NGK-01",
        price=Decimal("120000.00"),
        original_price=Decimal("150000.00"),
        status="ACTIVE",
    )
    return book


@pytest.fixture
def sample_inventory(sample_book):
    inv = Inventory(
        id=1,
        book_id=101,
        physical_stock=10,
        reserved_stock=2,
        low_stock_threshold=3,
    )
    inv.book = sample_book
    return inv


# ============================================================================
# 1. CHECKOUT & AUTHORITATIVE PRICING TESTS
# ============================================================================

def test_checkout_success_cod(mock_db, customer_user, sample_book, sample_inventory):
    """Test standard checkout with COD payment method and authoritative calculation."""
    app.dependency_overrides[get_current_user] = lambda: customer_user
    app.dependency_overrides[get_db] = lambda: mock_db

    cart = Cart(id=1, user_id=customer_user.id)
    cart_item = CartItem(
        id=1, cart_id=1, book_id=sample_book.id, quantity=2
    )
    cart_item.book = sample_book
    cart.items = [cart_item]

    # Mock DB query chains
    mock_db.query.return_value.filter.return_value.first.return_value = None  # idempotency check
    
    # CartRepository.get_or_create mock
    cart_query_mock = MagicMock()
    cart_query_mock.options.return_value.filter.return_value.first.return_value = cart
    
    # Inventory query with_for_update mock
    inv_query_mock = MagicMock()
    inv_query_mock.filter.return_value.with_for_update.return_value.first.return_value = sample_inventory
    inv_query_mock.filter.return_value.first.return_value = sample_inventory
    
    # Book query mock
    book_query_mock = MagicMock()
    book_query_mock.filter.return_value.first.return_value = sample_book

    def query_router(model):
        if model == Cart:
            return cart_query_mock
        elif model == Inventory:
            return inv_query_mock
        elif model == Book:
            return book_query_mock
        elif model == Order:
            m = MagicMock()
            m.filter.return_value.first.return_value = None
            return m
        return MagicMock()

    mock_db.query.side_effect = query_router

    payload = {
        "recipient_name": "Nguyễn Văn Nhận",
        "recipient_phone": "0987654321",
        "shipping_province": "Hà Nội",
        "shipping_district": "Cầu Giấy",
        "shipping_ward": "Dịch Vọng Hậu",
        "shipping_street_address": "Số 10 Phạm Văn Đồng",
        "customer_notes": "Giao giờ hành chính",
        "payment_method": "COD",
    }

    try:
        response = client.post("/api/v1/orders/checkout", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["order_code"].startswith("NVL-")
        assert Decimal(str(data["subtotal_amount"])) == Decimal("240000.00")  # 2 * 120,000
        assert Decimal(str(data["shipping_fee"])) == Decimal("30000.00")
        assert Decimal(str(data["total_amount"])) == Decimal("270000.00")
        assert data["status"] == "CONFIRMED"  # COD order auto-confirms
        assert data["payment_method"] == "COD"
        assert sample_inventory.reserved_stock == 4  # 2 + 2 reserved
    finally:
        app.dependency_overrides.clear()


def test_checkout_rejects_insufficient_stock(mock_db, customer_user, sample_book, sample_inventory):
    """Test checkout rejection when requested quantity exceeds available stock."""
    app.dependency_overrides[get_current_user] = lambda: customer_user
    app.dependency_overrides[get_db] = lambda: mock_db

    # Only 8 available (10 physical - 2 reserved)
    cart = Cart(id=1, user_id=customer_user.id)
    cart_item = CartItem(
        id=1, cart_id=1, book_id=sample_book.id, quantity=9  # Requesting 9 > 8 available
    )
    cart_item.book = sample_book
    cart.items = [cart_item]

    cart_query_mock = MagicMock()
    cart_query_mock.options.return_value.filter.return_value.first.return_value = cart
    
    inv_query_mock = MagicMock()
    inv_query_mock.filter.return_value.with_for_update.return_value.first.return_value = sample_inventory

    def query_router(model):
        if model == Cart:
            return cart_query_mock
        elif model == Inventory:
            return inv_query_mock
        elif model == Order:
            m = MagicMock()
            m.filter.return_value.first.return_value = None
            return m
        return MagicMock()

    mock_db.query.side_effect = query_router

    payload = {
        "recipient_name": "Nguyễn Văn Nhận",
        "recipient_phone": "0987654321",
        "shipping_province": "Hà Nội",
        "shipping_district": "Cầu Giấy",
        "shipping_ward": "Dịch Vọng",
        "shipping_street_address": "Số 10 Xuân Thủy",
        "payment_method": "COD",
    }

    try:
        response = client.post("/api/v1/orders/checkout", json=payload)
        assert response.status_code == 400
        assert "không đủ số lượng yêu cầu" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


# ============================================================================
# 2. PROMO CODE / COUPON VALIDATION TESTS
# ============================================================================

def test_coupon_validation_rules(mock_db, customer_user):
    """Test coupon expiration, min order value, and percentage discount logic."""
    now = datetime.now(timezone.utc)
    active_coupon = Coupon(
        id=1,
        code="GIAM20",
        discount_type="PERCENTAGE",
        discount_value=Decimal("20.00"),
        min_order_value=Decimal("200000.00"),
        max_discount_value=Decimal("50000.00"),
        usage_limit=100,
        used_count=5,
        start_date=now - timedelta(days=2),
        end_date=now + timedelta(days=5),
        is_active=True,
    )

    expired_coupon = Coupon(
        id=2,
        code="HETHAN",
        discount_type="FIXED_AMOUNT",
        discount_value=Decimal("30000.00"),
        min_order_value=Decimal("100000.00"),
        start_date=now - timedelta(days=10),
        end_date=now - timedelta(days=1),
        is_active=True,
    )

    # 1. Valid coupon meets min order value
    mock_db.query.return_value.filter.return_value.first.return_value = active_coupon
    mock_db.query.return_value.filter.return_value.count.return_value = 0  # user usage count
    
    res = OrderService.validate_coupon(
        mock_db, "GIAM20", user_id=customer_user.id, cart_subtotal=Decimal("300000.00")
    )
    assert res.is_valid is True
    # 20% of 300,000 = 60,000 -> capped at max_discount 50,000
    assert res.discount_amount == Decimal("50000.00")

    # 2. Below min order value
    res_below = OrderService.validate_coupon(
        mock_db, "GIAM20", user_id=customer_user.id, cart_subtotal=Decimal("150000.00")
    )
    assert res_below.is_valid is False
    assert "tối thiểu" in res_below.message

    # 3. Expired coupon
    mock_db.query.return_value.filter.return_value.first.return_value = expired_coupon
    res_exp = OrderService.validate_coupon(
        mock_db, "HETHAN", user_id=customer_user.id, cart_subtotal=Decimal("200000.00")
    )
    assert res_exp.is_valid is False
    assert "hết hạn sử dụng" in res_exp.message


# ============================================================================
# 3. IDEMPOTENCY & REPLAY ATTACK PREVENTION TESTS
# ============================================================================

def test_idempotent_order_submission(mock_db, customer_user, sample_book):
    """Test that duplicate requests with the same idempotency key return the existing order."""
    app.dependency_overrides[get_current_user] = lambda: customer_user
    app.dependency_overrides[get_db] = lambda: mock_db

    existing_order = Order(
        id=55,
        order_code="NVL-20261020-EXIST1",
        user_id=customer_user.id,
        subtotal_amount=Decimal("120000.00"),
        shipping_fee=Decimal("30000.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("150000.00"),
        status="CONFIRMED",
        recipient_name="Khách Hàng",
        recipient_phone="0987654321",
        shipping_province="Hà Nội",
        shipping_district="Cầu Giấy",
        shipping_ward="Dịch Vọng",
        shipping_street_address="Số 10 Duy Tân",
        staff_notes="IDEMPOTENCY:unique-key-12345",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    payment = Payment(
        id=55,
        payment_code="PAY-55",
        payment_method="COD",
        payment_status="PENDING",
        amount=Decimal("150000.00"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    existing_order.payment = payment
    existing_order.items = []

    order_query_mock = MagicMock()
    order_query_mock.options.return_value.filter.return_value.first.return_value = existing_order
    mock_db.query.return_value = order_query_mock

    payload = {
        "recipient_name": "Khách Hàng",
        "recipient_phone": "0987654321",
        "shipping_province": "Hà Nội",
        "shipping_district": "Cầu Giấy",
        "shipping_ward": "Dịch Vọng",
        "shipping_street_address": "Số 10 Duy Tân",
        "payment_method": "COD",
        "idempotency_key": "unique-key-12345",
    }

    try:
        response = client.post("/api/v1/orders/checkout", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["order_code"] == "NVL-20261020-EXIST1"
    finally:
        app.dependency_overrides.clear()


# ============================================================================
# 4. ORDER CANCELLATION & INVENTORY RESTORATION TESTS
# ============================================================================

def test_customer_can_cancel_pending_order_and_restores_stock(mock_db, customer_user, sample_inventory):
    """Test customer cancelling their own PENDING order releases reserved stock."""
    app.dependency_overrides[get_current_user] = lambda: customer_user
    app.dependency_overrides[get_db] = lambda: mock_db

    order = Order(
        id=77,
        order_code="NVL-CANCEL-01",
        user_id=customer_user.id,
        subtotal_amount=Decimal("120000.00"),
        shipping_fee=Decimal("30000.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("150000.00"),
        status="PENDING",
        recipient_name="Khách",
        recipient_phone="0912345678",
        shipping_province="Hà Nội",
        shipping_district="Đống Đa",
        shipping_ward="Láng Hạ",
        shipping_street_address="12 Huỳnh Thúc Kháng",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    item = OrderItem(
        id=1,
        order_id=77,
        book_id=101,
        book_title_snapshot="Nhà Giả Kim",
        book_isbn_snapshot="978-604-00-1111-1",
        book_sku_snapshot="NVL-NGK-01",
        price_at_purchase=Decimal("120000.00"),
        quantity=3,
        subtotal=Decimal("360000.00"),
        created_at=datetime.now(timezone.utc),
    )
    order.items = [item]
    order.payment = Payment(
        id=77,
        payment_code="PAY-77",
        payment_method="COD",
        payment_status="PENDING",
        amount=Decimal("150000.00"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    order.coupon_usages = []

    sample_inventory.reserved_stock = 5  # Currently 5 reserved

    order_query_mock = MagicMock()
    order_query_mock.options.return_value.filter.return_value.first.return_value = order
    inv_query_mock = MagicMock()
    inv_query_mock.filter.return_value.with_for_update.return_value.first.return_value = sample_inventory

    def query_router(model):
        if model == Order:
            return order_query_mock
        elif model == Inventory:
            return inv_query_mock
        return MagicMock()

    mock_db.query.side_effect = query_router

    try:
        response = client.post(
            "/api/v1/orders/NVL-CANCEL-01/cancel",
            json={"reason": "Tôi đặt nhầm địa chỉ giao hàng"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CANCELLED"
        assert sample_inventory.reserved_stock == 2  # 5 - 3 = 2 restored!
    finally:
        app.dependency_overrides.clear()


def test_customer_cannot_cancel_shipped_order(mock_db, customer_user):
    """Test customer cannot cancel orders that are already confirmed, processing, or shipping."""
    app.dependency_overrides[get_current_user] = lambda: customer_user
    app.dependency_overrides[get_db] = lambda: mock_db

    order = Order(
        id=88,
        order_code="NVL-SHIPPING-01",
        user_id=customer_user.id,
        subtotal_amount=Decimal("100000.00"),
        shipping_fee=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("100000.00"),
        status="SHIPPING",
        recipient_name="Khách",
        recipient_phone="0912345678",
        shipping_province="Hà Nội",
        shipping_district="Đống Đa",
        shipping_ward="Láng Hạ",
        shipping_street_address="12 Huỳnh Thúc Kháng",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    order.items = []
    order.coupon_usages = []

    order_query_mock = MagicMock()
    order_query_mock.options.return_value.filter.return_value.first.return_value = order
    mock_db.query.return_value = order_query_mock

    try:
        response = client.post(
            "/api/v1/orders/NVL-SHIPPING-01/cancel",
            json={"reason": "Không muốn mua nữa"},
        )
        assert response.status_code == 400
        assert "Khách hàng chỉ có thể hủy đơn khi ở trạng thái Chờ xử lý" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


# ============================================================================
# 5. MULTI-TENANT ISOLATION TESTS
# ============================================================================

def test_tenant_isolation_cannot_view_others_orders(mock_db, customer_user, other_customer):
    """Verify customer A receives 404 when querying customer B's order."""
    app.dependency_overrides[get_current_user] = lambda: customer_user
    app.dependency_overrides[get_db] = lambda: mock_db

    # Order belongs to other_customer (id=20)
    order = Order(
        id=99,
        order_code="NVL-OTHER-USER",
        user_id=other_customer.id,
        subtotal_amount=Decimal("50000.00"),
        shipping_fee=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("50000.00"),
        status="PENDING",
        recipient_name="Trần Khách",
        recipient_phone="0909090909",
        shipping_province="Hồ Chí Minh",
        shipping_district="Quận 1",
        shipping_ward="Bến Nghé",
        shipping_street_address="1 Lê Duẩn",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # When filtered by user_id=10, query returns None
    order_query_mock = MagicMock()
    order_query_mock.options.return_value.filter.return_value.filter.return_value.first.return_value = None
    mock_db.query.return_value = order_query_mock

    try:
        response = client.get("/api/v1/orders/NVL-OTHER-USER")
        assert response.status_code == 404
        assert "Không tìm thấy đơn hàng" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


# ============================================================================
# 6. PAYMENT WEBHOOK & IDEMPOTENT REPLAY TESTS
# ============================================================================

def test_payment_webhook_verifies_signature_and_marks_paid(mock_db, customer_user):
    """Test payment webhook updates status to PAID when signature is valid."""
    app.dependency_overrides[get_db] = lambda: mock_db

    order = Order(
        id=123,
        order_code="NVL-20261020-PAY01",
        user_id=customer_user.id,
        subtotal_amount=Decimal("200000.00"),
        shipping_fee=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("200000.00"),
        status="PENDING",
        recipient_name="Khách Hàng",
        recipient_phone="0987654321",
        shipping_province="Hà Nội",
        shipping_district="Cầu Giấy",
        shipping_ward="Dịch Vọng",
        shipping_street_address="10 Duy Tân",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    payment = Payment(
        id=123,
        payment_code="PAY-123",
        payment_method="MOCK",
        payment_status="PENDING",
        amount=Decimal("200000.00"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    order.payment = payment

    order_query_mock = MagicMock()
    order_query_mock.options.return_value.filter.return_value.first.return_value = order
    mock_db.query.return_value = order_query_mock

    # Compute valid signature
    valid_sig = compute_mock_signature(order.order_code, "200000.00")

    payload = {
        "order_code": order.order_code,
        "amount": "200000.00",
        "is_success": True,
        "transaction_id": "MOCK-TX-SUCCESS-999",
        "sig": valid_sig,
    }

    try:
        response = client.post("/api/v1/payments/webhook/mock", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert payment.payment_status == "PAID"
        assert order.status == "CONFIRMED"
    finally:
        app.dependency_overrides.clear()


def test_payment_webhook_rejects_invalid_signature(mock_db):
    """Test webhook rejects forged or tampered signatures with HTTP 400."""
    app.dependency_overrides[get_db] = lambda: mock_db

    payload = {
        "order_code": "NVL-FORGED-01",
        "amount": "200000.00",
        "is_success": True,
        "sig": "tampered_fake_signature_abc123",
    }

    try:
        response = client.post("/api/v1/payments/webhook/mock", json=payload)
        assert response.status_code == 400
        assert "Chữ ký xác thực cổng thanh toán không hợp lệ" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_payment_webhook_idempotent_replay_protection(mock_db, customer_user):
    """Test webhook gracefully handles duplicate/replay callbacks for already paid orders."""
    app.dependency_overrides[get_db] = lambda: mock_db

    order = Order(
        id=124,
        order_code="NVL-20261020-ALREADYPAID",
        user_id=customer_user.id,
        subtotal_amount=Decimal("150000.00"),
        shipping_fee=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("150000.00"),
        status="CONFIRMED",
        recipient_name="Khách Hàng",
        recipient_phone="0987654321",
        shipping_province="Hà Nội",
        shipping_district="Cầu Giấy",
        shipping_ward="Dịch Vọng",
        shipping_street_address="10 Duy Tân",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    # Payment already marked PAID
    payment = Payment(
        id=124,
        payment_code="PAY-124",
        payment_method="MOCK",
        payment_status="PAID",
        amount=Decimal("150000.00"),
        paid_at=datetime.now(timezone.utc),
        transaction_id="TX-PREVIOUSLY-RECEIVED",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    order.payment = payment

    order_query_mock = MagicMock()
    order_query_mock.options.return_value.filter.return_value.first.return_value = order
    mock_db.query.return_value = order_query_mock

    valid_sig = compute_mock_signature(order.order_code, "150000.00")

    payload = {
        "order_code": order.order_code,
        "amount": "150000.00",
        "is_success": True,
        "sig": valid_sig,
    }

    try:
        response = client.post("/api/v1/payments/webhook/mock", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "already_paid"
        assert "Giao dịch đã được ghi nhận thanh toán trước đó" in data["message"]
    finally:
        app.dependency_overrides.clear()
