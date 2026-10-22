"""Unit and Integration tests for Phase 9 — Novelia AI Assistant Ecosystem.

Validates:
- Realism rule: AI Provider health diagnostics and missing API key handling.
- Deterministic mock provider and intent recognition.
- Tool calling schemas & execution: Catalog search, book details, real-time stock, shipping guide.
- Mutating cart operations via business service with auth verification.
- Customer order history and tracking with anti-IDOR isolation.
- Persistent AI Action Audit Logging (`ai_action_logs`) with masked arguments.
- Safety Guardrails: Length boundary, rate limiting, and graceful timeout handling.
- Conversation session history endpoints.
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import (
    get_current_active_user,
    get_current_user,
    get_current_user_optional,
    get_db,
)
from app.core.config import settings
from app.integrations.ai.base import ToolCall
from app.integrations.ai.factory import get_ai_provider
from app.integrations.ai.guardrails import AIGuardrails, _rate_limit_cache
from app.integrations.ai.mock import MockAIProvider
from app.main import app
from app.models.ai import AIActionLog, AIConversation, AIMessage
from app.models.catalog import Book, Category
from app.models.commerce import Cart, CartItem, Order
from app.models.inventory import Inventory
from app.models.payment_shipping import Payment, Shipment
from app.models.user import Role, User, UserRole

client = TestClient(app)


def make_user(user_id: int, role_name: str = "CUSTOMER") -> User:
    """Helper to mock a User with assigned role."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = f"{role_name.lower()}_{user_id}@novelia.vn"
    user.full_name = f"Nguyễn Văn Đọc ({role_name})"
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
def mock_db():
    db = MagicMock()
    conv = MagicMock(spec=AIConversation)
    conv.id = 1
    conv.session_uuid = "nvl_conv_test_123"
    conv.user_id = 10
    conv.title = "Cuộc trò chuyện mới"
    conv.conversation_type = "ASSISTANT"
    conv.messages = []
    conv.created_at = datetime.now(timezone.utc)
    conv.updated_at = datetime.now(timezone.utc)

    msg = MagicMock(spec=AIMessage)
    msg.id = 1
    msg.conversation_id = 1
    msg.sender = "USER"
    msg.content = "Chào Novelia"
    msg.tool_calls = None
    msg.tool_results = None
    msg.created_at = datetime.now(timezone.utc)

    def query_router(model):
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.limit.return_value = q
        if model == AIConversation:
            q.first.return_value = conv
            q.all.return_value = [conv]
        elif model == AIMessage:
            q.first.return_value = None
            q.all.return_value = []
        elif model == Book:
            book_mock = MagicMock(spec=Book, id=1, title="Sách Lập Trình Python")
            q.first.return_value = book_mock
            q.all.return_value = [book_mock]
        else:
            q.first.return_value = None
            q.all.return_value = []
        return q

    db.query.side_effect = query_router
    return db


@pytest.fixture(autouse=True)
def reset_rate_limit_cache():
    _rate_limit_cache.clear()
    yield
    _rate_limit_cache.clear()


# ==============================================================================
# 1. HEALTH AND DIAGNOSTICS TESTS (REALISM RULE)
# ==============================================================================

def test_ai_health_endpoint_mock_ready():
    """Verify health endpoint accurately reports mock status when configured as mock."""
    with patch.object(settings, "AI_PROVIDER", "mock"):
        res = client.get("/api/v1/ai/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "MOCK_READY"
        assert data["provider"] == "mock"
        assert data["is_configured"] is True


def test_ai_health_endpoint_missing_api_key_realism():
    """Verify that when GEMINI is selected without key, status reports MISSING_API_KEY honestly."""
    with patch.object(settings, "AI_PROVIDER", "gemini"):
        with patch.object(settings, "GEMINI_API_KEY", ""):
            res = client.get("/api/v1/ai/health")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "MISSING_API_KEY"
            assert data["is_configured"] is False
            assert "GEMINI_API_KEY" in data["details"]


# ==============================================================================
# 2. INTENT & TOOL CALLING EXECUTION TESTS
# ==============================================================================

def test_ai_chat_catalog_search_tool(customer_user, mock_db):
    """Verify searching for books invokes search_catalog_tool and delivers book recommendations."""
    app.dependency_overrides[get_current_user_optional] = lambda: customer_user
    app.dependency_overrides[get_db] = lambda: mock_db

    sample_book = MagicMock(spec=Book)
    sample_book.id = 1
    sample_book.title = "Đắc Nhân Tâm"
    sample_book.slug = "dac-nhan-tam"
    sample_book.isbn = "9781234567890"
    sample_book.sku = "SKU-DACNHANTAM"
    sample_book.status = "ACTIVE"
    sample_book.format = "Bìa mềm"
    sample_book.cover_type = "PAPERBACK"
    sample_book.page_count = 320
    sample_book.price = Decimal("88000.00")
    sample_book.original_price = Decimal("110000.00")
    sample_book.cover_image_url = "https://images.unsplash.com/dac-nhan-tam.jpg"
    sample_book.authors = []
    sample_book.categories = []
    sample_book.inventory = MagicMock(available_stock=25)

    with patch("app.repositories.catalog_repo.BookRepository.list_books", return_value=([sample_book], 1)):
        res = client.post(
            "/api/v1/ai/chat",
            json={"message": "Tôi muốn tìm sách kinh tế dưới 150k", "session_uuid": "nvl_conv_test_123"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "Đắc Nhân Tâm" in data["message"]
        assert data["structured_payload"] is not None
        assert "books" in data["structured_payload"]
        assert len(data["structured_payload"]["books"]) == 1
        assert data["structured_payload"]["books"][0]["title"] == "Đắc Nhân Tâm"

    app.dependency_overrides.clear()


def test_ai_chat_stock_check_tool(customer_user, mock_db):
    """Verify checking book stock queries real inventory availability."""
    app.dependency_overrides[get_current_user_optional] = lambda: customer_user
    app.dependency_overrides[get_db] = lambda: mock_db

    sample_book = MagicMock(spec=Book)
    sample_book.id = 1
    sample_book.title = "Nhà Giả Kim"
    sample_book.price = Decimal("79000.00")
    sample_book.status = "ACTIVE"
    sample_book.inventory = MagicMock(
        physical_stock=50,
        reserved_stock=10,
        available_stock=40,
    )

    with patch("app.repositories.catalog_repo.BookRepository.get_by_id", return_value=sample_book):
        res = client.post(
            "/api/v1/ai/chat",
            json={"message": "Kiểm tra tồn kho sách 1", "session_uuid": "nvl_conv_test_123"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "Nhà Giả Kim" in data["message"]
        assert "40 cuốn" in data["message"]

    app.dependency_overrides.clear()


def test_ai_chat_shipping_guide_tool(customer_user, mock_db):
    """Verify customer asking about shipping policies receives accurate shipping threshold."""
    app.dependency_overrides[get_current_user_optional] = lambda: customer_user
    app.dependency_overrides[get_db] = lambda: mock_db

    res = client.post(
        "/api/v1/ai/chat",
        json={"message": "Chính sách phí vận chuyển và giao hàng như thế nào", "session_uuid": "nvl_conv_test_123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "500.000" in data["message"]
    assert "30.000" in data["message"]
    assert "GHN" in data["message"] or "GHTK" in data["message"]

    app.dependency_overrides.clear()


# ==============================================================================
# 3. AUTHENTICATION & SECURITY ENFORCEMENT
# ==============================================================================

def test_ai_chat_add_to_cart_authenticated(customer_user, mock_db):
    """Authenticated customer can add book to cart via AI tool."""
    app.dependency_overrides[get_current_user_optional] = lambda: customer_user
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_cart_read = MagicMock(total_items=2, subtotal_amount=Decimal("176000.00"))

    with patch("app.services.commerce_service.CartService.add_item", return_value=mock_cart_read):
        res = client.post(
            "/api/v1/ai/chat",
            json={"message": "Thêm sách 1 vào giỏ hàng", "session_uuid": "nvl_conv_test_123"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "giỏ hàng" in data["message"].lower()

    app.dependency_overrides.clear()


def test_ai_chat_add_to_cart_guest_rejected(mock_db):
    """Anonymous visitors cannot mutate cart without logging in."""
    app.dependency_overrides[get_current_user_optional] = lambda: None
    app.dependency_overrides[get_db] = lambda: mock_db

    res = client.post(
        "/api/v1/ai/chat",
        json={"message": "Thêm sách 1 vào giỏ hàng", "session_uuid": "nvl_conv_test_123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "đăng nhập" in data["message"].lower()

    app.dependency_overrides.clear()


def test_ai_chat_my_orders_authenticated(customer_user, mock_db):
    """Authenticated customer can query their own order history."""
    app.dependency_overrides[get_current_user_optional] = lambda: customer_user
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_order = MagicMock(spec=Order)
    mock_order.order_code = "NVL-20261020-TEST01"
    mock_order.status = "CONFIRMED"
    mock_order.total_amount = Decimal("250000.00")
    mock_order.created_at = datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc)
    mock_order.items = [MagicMock(quantity=2)]
    mock_order.payment = MagicMock(payment_method="COD", payment_status="PENDING")
    mock_order.shipment = None

    with patch("app.repositories.order_repo.OrderRepository.list_user_orders", return_value=([mock_order], 1)):
        res = client.post(
            "/api/v1/ai/chat",
            json={"message": "Cho tôi xem đơn hàng của tôi", "session_uuid": "nvl_conv_test_123"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "NVL-20261020-TEST01" in data["message"]
        assert "250,000" in data["message"]

    app.dependency_overrides.clear()


def test_ai_chat_my_orders_guest_rejected(mock_db):
    """Anonymous guest attempting to view personal orders is prompted to authenticate."""
    app.dependency_overrides[get_current_user_optional] = lambda: None
    app.dependency_overrides[get_db] = lambda: mock_db

    res = client.post(
        "/api/v1/ai/chat",
        json={"message": "Cho tôi xem đơn hàng của tôi", "session_uuid": "nvl_conv_test_123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "đăng nhập" in data["message"].lower()

    app.dependency_overrides.clear()


def test_ai_chat_anti_idor_order_tracking(customer_user, mock_db):
    """Customer cannot track an order belonging to another customer account (anti-IDOR)."""
    app.dependency_overrides[get_current_user_optional] = lambda: customer_user
    app.dependency_overrides[get_db] = lambda: mock_db

    # OrderRepository returns None when order does not match user_id
    with patch("app.repositories.order_repo.OrderRepository.get_by_code", return_value=None):
        res = client.post(
            "/api/v1/ai/chat",
            json={"message": "Theo dõi đơn hàng NVL-20261020-SECRET", "session_uuid": "nvl_conv_test_123"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "Không tìm thấy đơn hàng" in data["message"] or "không có quyền" in data["message"]

    app.dependency_overrides.clear()


# ==============================================================================
# 4. AUDIT TRAIL, GUARDRAILS & TIMEOUT TESTS
# ==============================================================================

def test_ai_action_audit_log_persisted(customer_user, mock_db):
    """Every tool call must record an AIActionLog entry in the database with duration and masked args."""
    app.dependency_overrides[get_current_user_optional] = lambda: customer_user
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("app.repositories.catalog_repo.BookRepository.list_books", return_value=([], 0)):
        res = client.post(
            "/api/v1/ai/chat",
            json={"message": "Tìm sách triết học", "session_uuid": "nvl_conv_test_123"},
        )
        assert res.status_code == 200

        # Verify db.add was called with an AIActionLog instance
        added_items = [args[0] for args, _ in mock_db.add.call_args_list]
        audit_logs = [item for item in added_items if isinstance(item, AIActionLog)]
        assert len(audit_logs) >= 1
        log = audit_logs[0]
        assert log.tool_name == "search_catalog_tool"
        assert log.user_role == "CUSTOMER"
        assert log.execution_status == "SUCCESS"
        assert log.execution_duration_ms is not None

    app.dependency_overrides.clear()


def test_ai_prompt_length_boundary_rejected():
    """Prompt exceeding 1000 characters is rejected with 400 or 422 Bad Request/Unprocessable Entity."""
    giant_prompt = "Sách " * 250  # > 1000 chars
    res = client.post(
        "/api/v1/ai/chat",
        json={"message": giant_prompt},
    )
    assert res.status_code in [400, 422]


def test_ai_rate_limiting_enforcement(mock_db):
    """Exceeding 20 requests per minute triggers 429 Too Many Requests."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user_optional] = lambda: None

    # Simulate 20 requests
    for _ in range(20):
        AIGuardrails.check_rate_limit("ip_test_rate_limiter", limit_per_minute=20)

    # 21st call should raise 429
    with pytest.raises(Exception) as exc_info:
        AIGuardrails.check_rate_limit("ip_test_rate_limiter", limit_per_minute=20)

    assert "quá nhiều yêu cầu" in str(exc_info.value.detail).lower()

    app.dependency_overrides.clear()


def test_ai_timeout_graceful_handling(customer_user, mock_db):
    """When the provider times out, AI Assistant returns a polite degradation error message."""
    app.dependency_overrides[get_current_user_optional] = lambda: customer_user
    app.dependency_overrides[get_db] = lambda: mock_db

    timeout_provider = MockAIProvider(simulate_timeout=True)

    with patch("app.services.ai_assistant_service.get_ai_provider", return_value=timeout_provider):
        res = client.post(
            "/api/v1/ai/chat",
            json={"message": "Tìm sách nào hay", "session_uuid": "nvl_conv_test_123"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "quá thời gian chờ" in data["message"].lower() or "timeout" in data["message"].lower()

    app.dependency_overrides.clear()


def test_ai_conversation_messages_history(customer_user, mock_db):
    """Retrieving conversation messages returns turn-by-turn history."""
    app.dependency_overrides[get_current_user_optional] = lambda: customer_user
    app.dependency_overrides[get_db] = lambda: mock_db

    msg1 = MagicMock(spec=AIMessage, id=1, sender="USER", content="Chào Novelia", tool_calls=None, tool_results=None, created_at=datetime.now(timezone.utc))
    msg2 = MagicMock(spec=AIMessage, id=2, sender="ASSISTANT", content="Dạ chào Quý khách!", tool_calls=None, tool_results=None, created_at=datetime.now(timezone.utc))

    q_mock = MagicMock()
    q_mock.filter.return_value = q_mock
    q_mock.order_by.return_value = q_mock
    q_mock.first.return_value = MagicMock(id=1, session_uuid="nvl_conv_test_123", user_id=10)
    q_mock.all.return_value = [msg1, msg2]
    mock_db.query.side_effect = None
    mock_db.query.return_value = q_mock

    res = client.get("/api/v1/ai/conversations/nvl_conv_test_123")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert data[0]["content"] == "Chào Novelia"
    assert data[1]["content"] == "Dạ chào Quý khách!"

    app.dependency_overrides.clear()
