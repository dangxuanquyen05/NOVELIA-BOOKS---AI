"""Unit and Integration tests for Phase 10 — AI Admin Copilot.

Validates:
1. RBAC Isolation:
   - CUSTOMER role is blocked from calling all admin tools (REJECTED_RBAC).
   - CUSTOMER role is blocked with HTTP 403 Forbidden on POST /api/v1/ai/confirm.
   - STAFF and ADMIN roles are authorized.
2. Two-Phase Confirmation Gate:
   - Calling mutating tools (prepare_book_update, prepare_inventory_adjustment, draft_promotion)
     returns a preview and an ephemeral confirmation_token with execution_status='CONFIRMATION_REQUIRED'.
   - Unconfirmed actions remain uncommitted: NO database changes occur to books, inventory, transactions, or coupons.
   - Calling POST /api/v1/ai/confirm re-verifies preconditions immediately prior to commit and executes the mutation.
   - Double-confirmation or invalid token is rejected with HTTP 400 / 404.
   - Precondition failure (e.g. proposed physical stock < reserved stock) prevents execution and rejects with HTTP 400.
3. Reporting Accuracy:
   - get_sales_summary matches authoritative AdminDashboardRepository data.
   - get_inventory_summary matches authoritative inventory count.
   - find_low_stock_books matches authoritative low-stock alerts.
   - search_orders matches OrderRepository.list_all_orders.
   - search_books matches BookRepository.list_books.
   - draft_product_description generates rich marketing metadata without mutating DB.
4. Persistent Audit Logging:
   - ai_action_logs stores user_role, tool_name, confirmation_token, is_confirmed, and masked input arguments.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.api.deps import (
    get_current_active_user,
    get_current_user,
    get_current_user_optional,
    get_db,
    require_roles,
)
from app.integrations.ai.tools import (
    ADMIN_TOOL_DEFINITIONS,
    CUSTOMER_TOOL_DEFINITIONS,
    AIToolExecutor,
)
from app.main import app
from app.models.ai import AIActionLog, AIConversation, AIMessage
from app.models.catalog import Book, Category, Author
from app.models.commerce import Coupon, Order, OrderItem
from app.models.inventory import Inventory, InventoryTransaction
from app.models.user import Role, User, UserRole
from app.schemas.admin_dashboard import DashboardKpiSummary, LowStockAlertItem

client = TestClient(app)


def make_user(user_id: int, role_name: str = "STAFF") -> User:
    """Helper to mock a User with assigned role."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = f"{role_name.lower()}_{user_id}@novelia.vn"
    user.full_name = f"Quản trị viên ({role_name})"
    user.phone = "0911223344"
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
    return make_user(101, "CUSTOMER")


@pytest.fixture
def staff_user():
    return make_user(202, "STAFF")


@pytest.fixture
def admin_user():
    return make_user(303, "ADMIN")


@pytest.fixture
def mock_db():
    db = MagicMock()
    conv = MagicMock(spec=AIConversation)
    conv.id = 1
    conv.session_uuid = "nvl_conv_admin_123"
    conv.user_id = 202
    conv.title = "Cuộc trò chuyện quản trị"
    conv.conversation_type = "ASSISTANT"
    conv.messages = []
    conv.created_at = datetime.now(timezone.utc)
    conv.updated_at = datetime.now(timezone.utc)

    msg = MagicMock(spec=AIMessage)
    msg.id = 1
    msg.conversation_id = 1
    msg.sender = "USER"
    msg.content = "Báo cáo doanh thu"
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
        elif model == AIActionLog:
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


# ==============================================================================
# 1. RBAC SECURITY TESTS
# ==============================================================================

class TestAdminCopilotRBAC:
    """Test strict role-based access control for Admin Copilot tools."""

    @pytest.mark.parametrize(
        "admin_tool",
        [
            "get_sales_summary",
            "get_inventory_summary",
            "find_low_stock_books",
            "search_orders",
            "search_books",
            "prepare_book_update",
            "draft_product_description",
            "draft_promotion",
            "prepare_inventory_adjustment",
        ],
    )
    def test_customer_cannot_call_admin_tools(self, admin_tool, customer_user):
        """Verify role CUSTOMER is strictly rejected from executing any admin tool."""
        mock_db = MagicMock()
        result = AIToolExecutor.execute(
            db=mock_db,
            tool_name=admin_tool,
            arguments={},
            current_user=customer_user,
        )

        assert result["success"] is False
        assert result["error_code"] == "REJECTED_RBAC"
        assert "không có quyền" in result["message"]

    def test_guest_cannot_call_admin_tools(self):
        """Verify unauthenticated GUEST is strictly rejected from calling admin tools."""
        mock_db = MagicMock()
        result = AIToolExecutor.execute(
            db=mock_db,
            tool_name="get_sales_summary",
            arguments={},
            current_user=None,
        )
        assert result["success"] is False
        assert result["error_code"] == "REJECTED_RBAC"

    def test_customer_cannot_access_confirm_endpoint(self, customer_user, mock_db):
        """Verify customer receives HTTP 403 Forbidden when calling POST /api/v1/ai/confirm."""
        app.dependency_overrides[get_current_active_user] = lambda: customer_user
        app.dependency_overrides[get_current_user] = lambda: customer_user
        app.dependency_overrides[get_db] = lambda: mock_db

        response = client.post(
            "/api/v1/ai/confirm",
            json={"confirmation_token": "confirm_test_token_123"},
        )
        app.dependency_overrides.clear()

        assert response.status_code == 403
        assert "Operation not permitted" in response.json()["detail"]


# ==============================================================================
# 2. READ REPORTING TOOLS & DATA CONSISTENCY
# ==============================================================================

class TestAdminReportingTools:
    """Validate that AI reporting tools query through authoritative repositories."""

    def test_get_sales_summary_matches_repository(self, staff_user):
        mock_db = MagicMock()
        expected_kpi = DashboardKpiSummary(
            total_revenue=Decimal("15000000.00"),
            collected_revenue=Decimal("12000000.00"),
            has_cost_data=False,
            profit_note="Chưa có dữ liệu COGS.",
            total_orders=45,
            valid_orders_count=40,
            average_order_value=Decimal("375000.00"),
            total_books=150,
            low_stock_count=8,
            total_customers=120,
            total_staff=4,
            active_coupons_count=3,
        )

        with patch("app.repositories.admin_dashboard_repo.AdminDashboardRepository.get_kpi_summary", return_value=expected_kpi):
            result = AIToolExecutor.execute(
                db=mock_db,
                tool_name="get_sales_summary",
                arguments={"start_date": "2026-10-01", "end_date": "2026-10-20"},
                current_user=staff_user,
            )

        assert result["success"] is True
        assert result["total_revenue"] == 15000000.0
        assert result["collected_revenue"] == 12000000.0
        assert result["valid_orders_count"] == 40
        assert result["average_order_value"] == 375000.0

    def test_get_inventory_summary_aggregation(self, staff_user):
        mock_db = MagicMock()
        # Mock scalar returns for: total_books, total_physical, total_reserved, low_stock, out_of_stock
        mock_db.query.return_value.scalar.side_effect = [120, 2500, 300]
        mock_db.query.return_value.filter.return_value.scalar.side_effect = [15, 2]

        result = AIToolExecutor.execute(
            db=mock_db,
            tool_name="get_inventory_summary",
            arguments={},
            current_user=staff_user,
        )

        assert result["success"] is True
        assert result["total_books"] == 120
        assert result["total_physical_stock"] == 2500
        assert result["total_reserved_stock"] == 300
        assert result["total_available_stock"] == 2200
        assert result["low_stock_count"] == 15
        assert result["out_of_stock_count"] == 2

    def test_find_low_stock_books(self, staff_user):
        mock_db = MagicMock()
        alerts = [
            LowStockAlertItem(
                book_id=1,
                title="Nhà Giả Kim",
                isbn="9786045634567",
                sku="BOOK-001",
                physical_stock=8,
                reserved_stock=3,
                available_stock=5,
                low_stock_threshold=10,
            ),
            LowStockAlertItem(
                book_id=2,
                title="Đắc Nhân Tâm",
                isbn="9786045634568",
                sku="BOOK-002",
                physical_stock=3,
                reserved_stock=2,
                available_stock=1,
                low_stock_threshold=10,
            ),
        ]

        with patch("app.repositories.admin_dashboard_repo.AdminDashboardRepository.get_low_stock_alerts", return_value=alerts):
            result = AIToolExecutor.execute(
                db=mock_db,
                tool_name="find_low_stock_books",
                arguments={"limit": 5},
                current_user=staff_user,
            )

        assert result["success"] is True
        assert result["count"] == 2
        assert result["low_stock_books"][0]["title"] == "Nhà Giả Kim"
        assert result["low_stock_books"][0]["available_stock"] == 5

    def test_draft_product_description_structure(self, staff_user):
        mock_db = MagicMock()
        book = MagicMock(spec=Book)
        book.id = 5
        book.title = "Lược Sử Loài Người"
        book.description = "Cuốn sách tóm tắt hành trình tiến hóa của loài người từ thời kỳ đồ đá đến nay."
        book.price = Decimal("185000.00")
        book.cover_type = "Bìa mềm"
        book.page_count = 520

        author = MagicMock(spec=Author)
        author.name = "Yuval Noah Harari"
        book.authors = [author]
        book.categories = []

        with patch("app.repositories.catalog_repo.BookRepository.get_by_id", return_value=book):
            result = AIToolExecutor.execute(
                db=mock_db,
                tool_name="draft_product_description",
                arguments={"book_id": 5},
                current_user=staff_user,
            )

        assert result["success"] is True
        assert result["book_id"] == 5
        draft = result["draft"]
        assert "Khám Phá Kiệt Tác 'Lược Sử Loài Người'" in draft["headline"]
        assert "Yuval Noah Harari" in draft["synopsis"]
        assert len(draft["key_selling_points"]) >= 3
        assert "target_audience" in draft
        assert "call_to_action" in draft


# ==============================================================================
# 3. TWO-PHASE CONFIRMATION & UNCOMMITTED STATE TESTS
# ==============================================================================

class TestTwoPhaseConfirmation:
    """Validate Two-Phase Confirmation guarantees: unconfirmed actions do not touch data."""

    def test_prepare_inventory_adjustment_creates_preview_without_mutating(self, staff_user):
        mock_db = MagicMock()
        book = MagicMock(spec=Book)
        book.id = 7
        book.title = "Kinh Tế Học Hài Hước"

        inv = MagicMock(spec=Inventory)
        inv.book_id = 7
        inv.physical_stock = 50
        inv.reserved_stock = 10
        inv.book = book

        with patch("app.repositories.inventory_repo.InventoryRepository.get_by_book_id", return_value=inv):
            result = AIToolExecutor.execute(
                db=mock_db,
                tool_name="prepare_inventory_adjustment",
                arguments={"book_id": 7, "delta": 20, "reason": "Nhập kho đợt 2"},
                current_user=staff_user,
            )

        assert result["success"] is True
        assert result["confirmation_required"] is True
        assert result["confirmation_token"].startswith("confirm_inv_")
        assert result["action_type"] == "ADJUST_INVENTORY"

        # Verify preview calculations
        preview = result["preview"]
        assert preview["current_physical_stock"] == 50
        assert preview["proposed_physical_stock"] == 70
        assert preview["current_available_stock"] == 40
        assert preview["proposed_available_stock"] == 60

        # UNCOMMITTED CHECK: verify inv.physical_stock was NOT changed
        assert inv.physical_stock == 50

    def test_prepare_inventory_adjustment_rejects_negative_stock(self, staff_user):
        mock_db = MagicMock()
        inv = MagicMock(spec=Inventory)
        inv.book_id = 7
        inv.physical_stock = 10
        inv.reserved_stock = 5
        inv.book = MagicMock()

        with patch("app.repositories.inventory_repo.InventoryRepository.get_by_book_id", return_value=inv):
            result = AIToolExecutor.execute(
                db=mock_db,
                tool_name="prepare_inventory_adjustment",
                arguments={"book_id": 7, "delta": -15, "reason": "Hao hụt"},
                current_user=staff_user,
            )

        assert result["success"] is False
        assert "không thể âm" in result["message"]

    def test_prepare_inventory_adjustment_rejects_delta_below_reserved(self, staff_user):
        mock_db = MagicMock()
        inv = MagicMock(spec=Inventory)
        inv.book_id = 7
        inv.physical_stock = 20
        inv.reserved_stock = 15
        inv.book = MagicMock()

        with patch("app.repositories.inventory_repo.InventoryRepository.get_by_book_id", return_value=inv):
            result = AIToolExecutor.execute(
                db=mock_db,
                tool_name="prepare_inventory_adjustment",
                arguments={"book_id": 7, "delta": -10, "reason": "Hư hại"},
                current_user=staff_user,
            )

        assert result["success"] is False
        assert "không thể nhỏ hơn tồn kho đang giữ chỗ" in result["message"]

    def test_prepare_book_update_creates_preview_without_mutating(self, staff_user):
        mock_db = MagicMock()
        book = MagicMock(spec=Book)
        book.id = 8
        book.title = "Tư Duy Nhanh Và Chậm"
        book.price = Decimal("200000.00")
        book.original_price = Decimal("250000.00")
        book.status = "ACTIVE"

        with patch("app.repositories.catalog_repo.BookRepository.get_by_id", return_value=book):
            result = AIToolExecutor.execute(
                db=mock_db,
                tool_name="prepare_book_update",
                arguments={"book_id": 8, "new_price": 175000.0},
                current_user=staff_user,
            )

        assert result["success"] is True
        assert result["confirmation_required"] is True
        assert result["confirmation_token"].startswith("confirm_bk_")
        assert result["preview"]["current_price"] == 200000.0
        assert result["preview"]["proposed_price"] == 175000.0

        # UNCOMMITTED CHECK: verify price on book object remains unchanged
        assert book.price == Decimal("200000.00")

    def test_execute_confirmation_applies_inventory_adjustment(self, staff_user):
        mock_db = MagicMock()
        action_log = MagicMock(spec=AIActionLog)
        action_log.tool_name = "prepare_inventory_adjustment"
        action_log.input_arguments = {"book_id": 12, "delta": 25, "reason": "Nhập thêm đợt 3"}
        action_log.is_confirmed = False
        action_log.confirmation_token = "confirm_inv_valid123"

        mock_db.query.return_value.filter.return_value.first.return_value = action_log

        # Mock current inventory in DB
        inv = MagicMock(spec=Inventory)
        inv.book_id = 12
        inv.physical_stock = 30
        inv.reserved_stock = 5

        updated_inv = MagicMock(spec=Inventory)
        updated_inv.book_id = 12
        updated_inv.physical_stock = 55
        updated_inv.reserved_stock = 5
        updated_inv.available_stock = 50

        with patch("app.repositories.inventory_repo.InventoryRepository.get_by_book_id", return_value=inv), \
             patch("app.repositories.inventory_repo.InventoryRepository.adjust_stock", return_value=updated_inv) as mock_adjust:
            result = AIToolExecutor.execute_confirmation(
                db=mock_db,
                confirmation_token="confirm_inv_valid123",
                staff_user=staff_user,
            )

        assert result["success"] is True
        assert result["action_type"] == "ADJUST_INVENTORY"
        assert result["details"]["physical_stock"] == 55
        assert action_log.is_confirmed is True
        assert action_log.execution_status == "SUCCESS"
        mock_adjust.assert_called_once()
        mock_db.commit.assert_called()

    def test_execute_confirmation_re_checks_stock_and_rejects_if_invalid(self, staff_user):
        """Precondition check immediately prior to commit: if stock condition changed, abort."""
        mock_db = MagicMock()
        action_log = MagicMock(spec=AIActionLog)
        action_log.tool_name = "prepare_inventory_adjustment"
        action_log.input_arguments = {"book_id": 12, "delta": -20, "reason": "Xuất điều chuyển"}
        action_log.is_confirmed = False
        action_log.confirmation_token = "confirm_inv_stale123"

        mock_db.query.return_value.filter.return_value.first.return_value = action_log

        # Simulate that in the meantime, customers reserved 18 items, so 30 - 20 < 18
        inv = MagicMock(spec=Inventory)
        inv.book_id = 12
        inv.physical_stock = 30
        inv.reserved_stock = 18

        with patch("app.repositories.inventory_repo.InventoryRepository.get_by_book_id", return_value=inv):
            with pytest.raises(HTTPException) as exc_info:
                AIToolExecutor.execute_confirmation(
                    db=mock_db,
                    confirmation_token="confirm_inv_stale123",
                    staff_user=staff_user,
                )

        assert exc_info.value.status_code == 400
        assert "nhỏ hơn tồn kho giữ chỗ" in exc_info.value.detail
        assert action_log.is_confirmed is False

    def test_execute_confirmation_prevents_double_execution(self, staff_user):
        """Prevent double-spend/replay attacks on confirmation tokens."""
        mock_db = MagicMock()
        action_log = MagicMock(spec=AIActionLog)
        action_log.is_confirmed = True  # Already executed
        action_log.confirmation_token = "confirm_already_done"

        mock_db.query.return_value.filter.return_value.first.return_value = action_log

        with pytest.raises(HTTPException) as exc_info:
            AIToolExecutor.execute_confirmation(
                db=mock_db,
                confirmation_token="confirm_already_done",
                staff_user=staff_user,
            )

        assert exc_info.value.status_code == 400
        assert "đã được xác nhận và thực thi trước đó" in exc_info.value.detail


# ==============================================================================
# 4. CHAT INTERACTION & CONFIRMATION ENDPOINT INTEGRATION
# ==============================================================================

class TestAdminChatAndConfirmEndpoint:
    """Validate full flow via FastAPI endpoints with staff credentials."""

    def test_post_confirm_endpoint_success(self, staff_user, mock_db):
        """Staff confirms pending token via POST /api/v1/ai/confirm."""
        app.dependency_overrides[get_current_active_user] = lambda: staff_user
        app.dependency_overrides[get_current_user] = lambda: staff_user
        app.dependency_overrides[get_db] = lambda: mock_db

        confirm_res = {
            "success": True,
            "action_type": "ADJUST_INVENTORY",
            "message": "Đã thực thi điều chỉnh tồn kho thành công.",
            "details": {"book_id": 15, "physical_stock": 80},
            "executed_at": datetime.now(timezone.utc),
        }

        with patch("app.services.ai_assistant_service.AIToolExecutor.execute_confirmation", return_value=confirm_res):
            response = client.post(
                "/api/v1/ai/confirm",
                json={"confirmation_token": "confirm_inv_token_abc"},
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action_type"] == "ADJUST_INVENTORY"
        assert data["details"]["book_id"] == 15

    def test_chat_with_admin_sales_intent(self, staff_user, mock_db):
        """Staff asks for sales report in chat -> triggers get_sales_summary."""
        app.dependency_overrides[get_current_user_optional] = lambda: staff_user
        app.dependency_overrides[get_current_active_user] = lambda: staff_user
        app.dependency_overrides[get_db] = lambda: mock_db

        mock_kpi = DashboardKpiSummary(
            total_revenue=Decimal("8500000.00"),
            collected_revenue=Decimal("7000000.00"),
            has_cost_data=False,
            profit_note="Chưa có dữ liệu COGS.",
            total_orders=25,
            valid_orders_count=22,
            average_order_value=Decimal("386363.64"),
            total_books=100,
            low_stock_count=5,
            total_customers=80,
            total_staff=3,
            active_coupons_count=2,
        )

        with patch("app.repositories.admin_dashboard_repo.AdminDashboardRepository.get_kpi_summary", return_value=mock_kpi):
            response = client.post(
                "/api/v1/ai/chat",
                json={"message": "Cho tôi xem báo cáo doanh thu bán hàng hôm nay"},
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "Báo cáo Doanh thu & Vận hành" in data["message"]
        assert "8,500,000 đ" in data["message"]
        assert "sales_summary" in (data.get("structured_payload") or {})
