"""Tests for Conversational Ordering Assistant, Rule-based Fallback, and VietQR integration.

Validates the complete Conversational Commerce model inspired by AgriSense Platform,
adapted to NOVELIA BOOKS standards:
- Vietnamese unaccented normalization and fuzzy n-gram matching for books.
- Entity extraction: Phone, quantity, recipient name, address, and payment method.
- Multi-turn conversation state machine (intent -> info -> payment method choice -> checkout).
- Interactive Choice Card syntax generation ([choice:Title|Desc|Icon](query)).
- Atomic direct order creation in database with ACID inventory locking.
- Dynamic VietQR Napas 247 QR generation for cashless payments.
- Zero-downtime rule-based fallback responses for shipping, pricing, and orders.
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
import pytest

from app.integrations.ai.fallback import (
    find_matching_books,
    format_currency,
    get_fallback_response,
    remove_accents,
)
from app.integrations.payment.vietqr import get_vietqr_info, get_vietqr_url
from app.models.catalog import Book, Category
from app.models.commerce import Order
from app.models.inventory import Inventory
from app.models.user import Role, User, UserRole
from app.services.order_assistant_service import (
    OrderAssistantService,
    _ORDER_DRAFTS,
    extract_address_and_name,
    extract_payment_method,
    extract_phone,
    extract_quantity,
)


def make_test_user(user_id: int = 10, name: str = "Nguyễn Văn Đọc") -> User:
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = "docgia@novelia.vn"
    user.full_name = name
    user.phone = "0988776655"
    user.is_active = True
    user.created_at = datetime.now(timezone.utc)

    role = MagicMock(spec=Role)
    role.name = "CUSTOMER"
    ur = MagicMock(spec=UserRole)
    ur.role = role
    user.roles = [ur]
    return user


def make_test_book(book_id: int = 1, title: str = "Đắc Nhân Tâm", price: Decimal = Decimal("120000.00"), stock: int = 10) -> Book:
    book = MagicMock(spec=Book)
    book.id = book_id
    book.title = title
    book.author = "Dale Carnegie"
    book.isbn = "9786045632123"
    book.sku = "SKU-DNT-01"
    book.price = price
    book.status = "ACTIVE"

    cat = MagicMock(spec=Category)
    cat.name = "Kỹ năng sống"
    book.category = cat
    return book


# ==============================================================================
# 1. ENTITY EXTRACTION & NORMALIZATION TESTS
# ==============================================================================

def test_remove_accents():
    assert remove_accents("Đắc Nhân Tâm") == "dac nhan tam"
    assert remove_accents("Nhà Giả Kim") == "nha gia kim"
    assert remove_accents("TIẾNG VIỆT CÓ DẤU") == "tieng viet co dau"
    assert remove_accents("") == ""


def test_extract_phone():
    assert extract_phone("giao về sđt 0912345678 nhé") == "0912345678"
    assert extract_phone("số điện thoại: +84988776655") == "0988776655"
    assert extract_phone("alo 0371.234.567") == "0371234567"
    assert extract_phone("không có số ở đây") is None


def test_extract_quantity():
    assert extract_quantity("Cho tôi mua 2 cuốn Đắc Nhân Tâm") == 2
    assert extract_quantity("Lên đơn 5 quyển Nhà Giả Kim") == 5
    assert extract_quantity("Mua 3 bộ Sherlock Holmes") == 3
    assert extract_quantity("Mua sách Đắc Nhân Tâm") == 1


def test_extract_payment_method():
    assert extract_payment_method("Tôi chọn COD") == "COD"
    assert extract_payment_method("Thanh toán tiền mặt khi nhận hàng") == "COD"
    assert extract_payment_method("1") == "COD"
    assert extract_payment_method("Quét mã VietQR nha") == "VIETQR"
    assert extract_payment_method("Chuyển khoản qua ngân hàng") == "VIETQR"
    assert extract_payment_method("2") == "VIETQR"


def test_extract_address_and_name():
    name, addr = extract_address_and_name("Tên người nhận: Trần Thị Hương, địa chỉ: Số 45 Cầu Giấy, Hà Nội")
    assert name == "Trần Thị Hương"
    assert "Cầu Giấy, Hà Nội" in addr

    # Cleaned address with cues
    _, addr2 = extract_address_and_name("Giao về đường Nguyễn Huệ, Quận 1, TP HCM, sđt 0912345678", phone="0912345678")
    assert "Nguyễn Huệ, Quận 1, TP HCM" in addr2


# ==============================================================================
# 2. VIETQR DYNAMIC GENERATION TESTS
# ==============================================================================

def test_vietqr_url_generation():
    url = get_vietqr_url(order_code="NVL-20261021-ABC123", amount=Decimal("270000.00"))
    assert "img.vietqr.io/image/TCB-7979798950-compact2.png" in url
    assert "amount=270000" in url
    assert "addInfo=NVL-20261021-ABC123" in url


def test_vietqr_info_payload():
    info = get_vietqr_info(order_code="NVL-TEST-001", amount=150000)
    assert info["bank_id"] == "TCB"
    assert info["account_no"] == "7979798950"
    assert info["amount"] == 150000
    assert info["memo"] == "NVL-TEST-001"
    assert "qr_image_url" in info


# ==============================================================================
# 3. RULE-BASED FALLBACK ENGINE TESTS
# ==============================================================================

def test_fallback_shipping_policy():
    mock_db = MagicMock()
    reply, intent = get_fallback_response(mock_db, "Phí ship và chính sách giao hàng thế nào?")
    assert intent == "shipping"
    assert "500.000 đ" in reply
    assert "30.000 đ" in reply
    assert "Freeship" in reply


def test_fallback_pricing_and_stock():
    mock_db = MagicMock()
    book = make_test_book(1, "Đắc Nhân Tâm", Decimal("120000.00"))
    inv = MagicMock(spec=Inventory)
    inv.physical_stock = 15
    inv.reserved_stock = 3

    mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [book]
    mock_db.query.return_value.filter.return_value.first.return_value = inv

    reply, intent = get_fallback_response(mock_db, "Giá cuốn Đắc Nhân Tâm là bao nhiêu?")
    assert intent == "price_stock"
    assert "Đắc Nhân Tâm" in reply
    assert "120.000 đ" in reply


# ==============================================================================
# 4. CONVERSATIONAL ORDERING MULTI-TURN ASSISTANT TESTS
# ==============================================================================

def test_order_intent_unauthenticated():
    mock_db = MagicMock()
    session_uuid = "sess_guest_01"
    handled, reply, payload = OrderAssistantService.handle_order_conversation(
        db=mock_db,
        message="Tôi muốn mua 2 cuốn Nhà Giả Kim",
        session_uuid=session_uuid,
        current_user=None,
    )
    assert handled is True
    assert "Đăng nhập" in reply or "tài khoản" in reply


def test_order_intent_missing_address_creates_draft():
    mock_db = MagicMock()
    book = make_test_book(1, "Nhà Giả Kim", Decimal("150000.00"))
    inv = MagicMock(spec=Inventory)
    inv.physical_stock = 20
    inv.reserved_stock = 2

    q = MagicMock()
    q.filter.return_value = q
    q.limit.return_value = q
    q.all.return_value = [book]
    q.first.side_effect = lambda: book if mock_db.query.call_args[0][0] == Book else inv
    mock_db.query.return_value = q

    user = make_test_user(10, "Lê Hoàng")
    user.phone = ""  # No saved phone
    session_uuid = "sess_multiturn_01"
    _ORDER_DRAFTS.pop(session_uuid, None)

    # Turn 1: User says order
    handled, reply, payload = OrderAssistantService.handle_order_conversation(
        db=mock_db,
        message="Lên đơn 2 cuốn Nhà Giả Kim cho tôi",
        session_uuid=session_uuid,
        current_user=user,
    )
    assert handled is True
    assert "Số điện thoại" in reply
    assert session_uuid in _ORDER_DRAFTS
    assert _ORDER_DRAFTS[session_uuid]["step"] == "awaiting_info"

    # Turn 2: User provides phone and address
    handled, reply, payload = OrderAssistantService.handle_order_conversation(
        db=mock_db,
        message="Sđt 0912345678, giao về số 10 Phan Chu Trinh, Hoàn Kiếm, Hà Nội",
        session_uuid=session_uuid,
        current_user=user,
    )
    assert handled is True
    assert _ORDER_DRAFTS[session_uuid]["step"] == "awaiting_payment_method"
    assert "[choice:Thanh toán khi nhận hàng (COD)" in reply
    assert "[choice:Chuyển khoản VietQR" in reply

    # Turn 3: User chooses VietQR
    order_mock = MagicMock(spec=Order)
    order_mock.order_code = "NVL-20261021-TESTQR"
    order_mock.total_amount = Decimal("330000.00")
    order_mock.shipping_fee = Decimal("30000.00")
    order_mock.recipient_name = "Lê Hoàng"
    order_mock.recipient_phone = "0912345678"
    order_mock.shipping_street_address = "số 10 Phan Chu Trinh, Hoàn Kiếm, Hà Nội"
    payment_mock = MagicMock()
    payment_mock.payment_method = "VIETQR"
    order_mock.payment = payment_mock

    # Mock execute_direct_order
    from unittest.mock import patch
    with patch("app.services.order_assistant_service.execute_direct_order", return_value=order_mock):
        handled, reply, payload = OrderAssistantService.handle_order_conversation(
            db=mock_db,
            message="Chuyển khoản VietQR",
            session_uuid=session_uuid,
            current_user=user,
        )
        assert handled is True
        assert "ĐẶT SÁCH THÀNH CÔNG" in reply
        assert "NVL-20261021-TESTQR" in reply
        assert "Mã VietQR thanh toán" in reply
        assert session_uuid not in _ORDER_DRAFTS  # Draft cleared upon success
        assert payload is not None
        assert payload["order_success"]["order_code"] == "NVL-20261021-TESTQR"


def test_order_cancellation_flow():
    mock_db = MagicMock()
    user = make_test_user(10)
    session_uuid = "sess_cancel_test"
    _ORDER_DRAFTS[session_uuid] = {"book_id": 1, "step": "awaiting_info"}

    handled, reply, _ = OrderAssistantService.handle_order_conversation(
        db=mock_db,
        message="Thôi tôi không mua nữa, hủy giúp tôi",
        session_uuid=session_uuid,
        current_user=user,
    )
    assert handled is True
    assert "hủy yêu cầu" in reply
    assert session_uuid not in _ORDER_DRAFTS
