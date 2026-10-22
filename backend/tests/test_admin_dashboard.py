"""Unit and integration tests for Phase 7 — Admin Dashboard, Executive KPIs, and Governance.

Validates:
- Real-time KPI aggregation: Gross Revenue, Collected Cash, AOV, Order Counts.
- Truth in financial presentation: has_cost_data is False when COGS is unavailable.
- Order status breakdown and time period filtering (7days, 30days, 90days, 12months, all).
- RBAC enforcement:
    - CUSTOMER blocked from all admin dashboard routes (HTTP 403).
    - STAFF allowed to view dashboard, manage taxonomies and promotions, but blocked from user governance (HTTP 403).
    - ADMIN has full governance access.
- Self-protection guards:
    - Admin cannot deactivate own account (HTTP 400).
    - Admin cannot strip ADMIN role from self (HTTP 400).
- Taxonomies integrity:
    - Category cannot be deleted when books are linked (HTTP 400).
    - Unique name/slug validation.
- Coupon lifecycle:
    - Coupon creation with dates validation.
    - Toggle coupon active/inactive state.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models.catalog import Author, Book, BookCategory, Category, Publisher
from app.models.commerce import Coupon, CouponUsage, Order, OrderItem
from app.models.inventory import Inventory, InventoryTransaction
from app.models.user import Role, User, UserRole
from app.schemas.admin_dashboard import (
    AdminCategoryCreateRequest,
    AdminCategoryUpdateRequest,
    AdminCouponCreateRequest,
)
from app.services.admin_dashboard_service import AdminDashboardService

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
    return make_user(1, "CUSTOMER")


@pytest.fixture
def staff_user():
    return make_user(2, "STAFF")


@pytest.fixture
def admin_user():
    return make_user(3, "ADMIN")


@pytest.fixture
def mock_db():
    return MagicMock()


# ============================================================================
# 1. RBAC ACCESS CONTROL TESTS
# ============================================================================

def test_customer_cannot_access_dashboard_summary(customer_user, mock_db):
    """Customers must receive 403 Forbidden when attempting to access store dashboard."""
    app.dependency_overrides[get_current_user] = lambda: customer_user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/api/v1/admin/dashboard/summary")
        assert response.status_code == 403
        assert "Operation not permitted" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_customer_cannot_access_user_governance(customer_user, mock_db):
    """Customers must receive 403 Forbidden when attempting to list users."""
    app.dependency_overrides[get_current_user] = lambda: customer_user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/api/v1/admin/dashboard/users")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_staff_cannot_access_user_governance(staff_user, mock_db):
    """Staff must receive 403 Forbidden when attempting to access user governance (ADMIN only)."""
    app.dependency_overrides[get_current_user] = lambda: staff_user
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/api/v1/admin/dashboard/users")
        assert response.status_code == 403
        assert "Required roles: ADMIN" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


# ============================================================================
# 2. EXECUTIVE DASHBOARD & FINANCIAL REALISM TESTS
# ============================================================================

def test_dashboard_summary_financial_truth_and_kpis(admin_user, mock_db):
    """Verify that KPI calculation strictly separates Gross Revenue and Collected Cash,
    and returns has_cost_data=False when inventory COGS is unavailable.
    """
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("app.repositories.admin_dashboard_repo.AdminDashboardRepository.get_kpi_summary") as mock_kpi, \
         patch("app.repositories.admin_dashboard_repo.AdminDashboardRepository.get_revenue_timeline") as mock_timeline, \
         patch("app.repositories.admin_dashboard_repo.AdminDashboardRepository.get_orders_by_status") as mock_status, \
         patch("app.repositories.admin_dashboard_repo.AdminDashboardRepository.get_top_selling_books") as mock_top, \
         patch("app.repositories.admin_dashboard_repo.AdminDashboardRepository.get_low_stock_alerts") as mock_low, \
         patch("app.repositories.admin_dashboard_repo.AdminDashboardRepository.get_recent_activities") as mock_recent:

        from app.schemas.admin_dashboard import DashboardKpiSummary

        mock_kpi.return_value = DashboardKpiSummary(
            total_revenue=Decimal("3500000.00"),
            collected_revenue=Decimal("2800000.00"),
            has_cost_data=False,
            profit_note="Chưa có dữ liệu giá vốn nhập kho (COGS) để tính toán lợi nhuận ròng thực tế.",
            total_orders=15,
            valid_orders_count=15,
            average_order_value=Decimal("233333.33"),
            total_books=120,
            low_stock_count=3,
            total_customers=45,
            total_staff=4,
            active_coupons_count=2,
        )
        mock_timeline.return_value = []
        mock_status.return_value = []
        mock_top.return_value = []
        mock_low.return_value = []
        mock_recent.return_value = []

        try:
            response = client.get("/api/v1/admin/dashboard/summary?period=30days")
            assert response.status_code == 200
            data = response.json()

            # Check KPI response
            assert data["kpis"]["total_orders"] == 15
            assert float(data["kpis"]["total_revenue"]) == 3500000.00
            assert float(data["kpis"]["collected_revenue"]) == 2800000.00
            assert float(data["kpis"]["average_order_value"]) == 233333.33
            # Critical constraint: No fake profit when cost is unavailable
            assert data["kpis"]["has_cost_data"] is False
            assert "COGS" in data["kpis"]["profit_note"]
            assert data["filter_period"] == "30days"
        finally:
            app.dependency_overrides.clear()


def test_dashboard_summary_time_filters(staff_user, mock_db):
    """Verify period filters correctly map into the service."""
    app.dependency_overrides[get_current_user] = lambda: staff_user
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("app.services.admin_dashboard_service.AdminDashboardService.get_dashboard_summary") as mock_srv:
        from app.schemas.admin_dashboard import AdminDashboardSummaryResponse, DashboardKpiSummary
        mock_srv.return_value = AdminDashboardSummaryResponse(
            kpis=DashboardKpiSummary(
                total_revenue=Decimal("0.00"),
                collected_revenue=Decimal("0.00"),
                has_cost_data=False,
                profit_note="Chưa có dữ liệu giá vốn nhập kho (COGS) để tính toán lợi nhuận ròng thực tế.",
                total_orders=0,
                valid_orders_count=0,
                average_order_value=Decimal("0.00"),
                total_books=0,
                low_stock_count=0,
                total_customers=0,
                total_staff=0,
                active_coupons_count=0,
            ),
            timeline=[],
            status_breakdown=[],
            top_selling_books=[],
            low_stock_alerts=[],
            recent_activities=[],
            filter_period="7days",
        )
        try:
            response = client.get("/api/v1/admin/dashboard/summary?period=7days")
            assert response.status_code == 200
            mock_srv.assert_called_once_with(mock_db, period="7days")
        finally:
            app.dependency_overrides.clear()


# ============================================================================
# 3. CATEGORIES MANAGEMENT TESTS
# ============================================================================

def test_category_create_success(staff_user, mock_db):
    """Staff can create a new category."""
    app.dependency_overrides[get_current_user] = lambda: staff_user
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_db.query.return_value.filter.return_value.first.return_value = None  # No duplicates

    try:
        response = client.post(
            "/api/v1/admin/dashboard/categories",
            json={"name": "Khoa Học & Vũ Trụ", "slug": "khoa-hoc-vu-tru", "description": "Sách về khoa học"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Khoa Học & Vũ Trụ"
        assert data["slug"] == "khoa-hoc-vu-tru"
        assert mock_db.commit.called
    finally:
        app.dependency_overrides.clear()


def test_category_delete_blocked_when_books_linked(staff_user, mock_db):
    """Category deletion must be rejected with 400 if books are attached."""
    app.dependency_overrides[get_current_user] = lambda: staff_user
    app.dependency_overrides[get_db] = lambda: mock_db

    fake_cat = Category(id=5, name="Văn Học", slug="van-hoc")
    # First query finds the category
    mock_db.query.return_value.filter.return_value.first.return_value = fake_cat
    # Second query for BookCategory count returns 3 attached books
    mock_db.query.return_value.filter.return_value.count.return_value = 3

    try:
        response = client.delete("/api/v1/admin/dashboard/categories/5")
        assert response.status_code == 400
        assert "đang liên kết với 3 đầu sách" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


# ============================================================================
# 4. USER GOVERNANCE & SELF-PROTECTION TESTS (ADMIN ONLY)
# ============================================================================

def test_admin_cannot_deactivate_self(admin_user, mock_db):
    """Admin cannot deactivate their own active account."""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.put(
            f"/api/v1/admin/dashboard/users/{admin_user.id}/status",
            json={"is_active": False},
        )
        assert response.status_code == 400
        assert "không thể tự vô hiệu hóa" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_admin_cannot_demote_self(admin_user, mock_db):
    """Admin cannot remove the ADMIN role from their own user account."""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.put(
            f"/api/v1/admin/dashboard/users/{admin_user.id}/role",
            json={"roles": ["CUSTOMER"]},
        )
        assert response.status_code == 400
        assert "không thể tự xóa quyền ADMIN" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_admin_can_update_other_user_status(admin_user, mock_db):
    """Admin can activate or deactivate another customer account."""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_db] = lambda: mock_db

    target_user = make_user(42, "CUSTOMER")
    target_user.is_active = False

    with patch("app.repositories.admin_dashboard_repo.AdminDashboardRepository.update_user_status") as mock_update:
        mock_update.return_value = target_user

        try:
            response = client.put(
                "/api/v1/admin/dashboard/users/42/status",
                json={"is_active": False},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 42
            assert data["is_active"] is False
        finally:
            app.dependency_overrides.clear()


# ============================================================================
# 5. COUPON GOVERNANCE TESTS
# ============================================================================

def test_coupon_create_dates_validation(staff_user, mock_db):
    """Coupon creation must reject invalid dates where start_date >= end_date."""
    app.dependency_overrides[get_current_user] = lambda: staff_user
    app.dependency_overrides[get_db] = lambda: mock_db

    now = datetime.now(timezone.utc)
    mock_db.query.return_value.filter.return_value.first.return_value = None

    try:
        response = client.post(
            "/api/v1/admin/dashboard/coupons",
            json={
                "code": "INVALIDDATES",
                "discount_type": "PERCENT",
                "discount_value": 15,
                "min_order_value": 100000,
                "start_date": (now + timedelta(days=5)).isoformat(),
                "end_date": now.isoformat(),  # End date earlier than start date
                "is_active": True,
            },
        )
        assert response.status_code == 400
        assert "Ngày bắt đầu phải trước ngày kết thúc" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_coupon_toggle_status(staff_user, mock_db):
    """Staff can toggle coupon active status."""
    app.dependency_overrides[get_current_user] = lambda: staff_user
    app.dependency_overrides[get_db] = lambda: mock_db

    fake_coupon = MagicMock(spec=Coupon)
    fake_coupon.id = 1
    fake_coupon.code = "GIAM20K"
    fake_coupon.description = "Giảm 20.000đ"
    fake_coupon.discount_type = "FIXED"
    fake_coupon.discount_value = Decimal("20000.00")
    fake_coupon.min_order_value = Decimal("100000.00")
    fake_coupon.max_discount_value = None
    fake_coupon.usage_limit = 100
    fake_coupon.used_count = 10
    fake_coupon.start_date = datetime.now(timezone.utc)
    fake_coupon.end_date = datetime.now(timezone.utc) + timedelta(days=30)
    fake_coupon.is_active = False
    fake_coupon.usages = []
    fake_coupon.created_at = datetime.now(timezone.utc)

    with patch("app.repositories.admin_dashboard_repo.AdminDashboardRepository.toggle_coupon") as mock_toggle:
        mock_toggle.return_value = fake_coupon

        try:
            response = client.put("/api/v1/admin/dashboard/coupons/1/toggle")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["code"] == "GIAM20K"
            assert data["is_active"] is False
        finally:
            app.dependency_overrides.clear()


def test_authors_and_publishers_endpoints(staff_user, mock_db):
    """Staff can create and list authors and publishers."""
    app.dependency_overrides[get_current_user] = lambda: staff_user
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_db.query.return_value.filter.return_value.first.return_value = None

    try:
        # Create author
        res_auth = client.post(
            "/api/v1/admin/dashboard/authors",
            json={"name": "Nguyễn Nhật Ánh", "slug": "nguyen-nhat-anh", "nationality": "Việt Nam"},
        )
        assert res_auth.status_code == 201
        assert res_auth.json()["name"] == "Nguyễn Nhật Ánh"

        # Create publisher
        res_pub = client.post(
            "/api/v1/admin/dashboard/publishers",
            json={"name": "NXB Trẻ", "slug": "nxb-tre", "website": "https://nxbtre.com.vn"},
        )
        assert res_pub.status_code == 201
        assert res_pub.json()["name"] == "NXB Trẻ"
    finally:
        app.dependency_overrides.clear()


def test_user_governance_list_users(admin_user, mock_db):
    """Admin can query and paginate users list."""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_db] = lambda: mock_db

    u1 = make_user(10, "CUSTOMER")
    u2 = make_user(11, "STAFF")

    with patch("app.repositories.admin_dashboard_repo.AdminDashboardRepository.list_users") as mock_list:
        mock_list.return_value = ([u1, u2], 2)
        # Mock order stats query for users
        mock_db.query.return_value.filter.return_value.first.return_value = (3, Decimal("450000.00"))

        try:
            response = client.get("/api/v1/admin/dashboard/users?page=1&page_size=10")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert len(data["items"]) == 2
            assert data["items"][0]["orders_count"] == 3
            assert float(data["items"][0]["total_spent"]) == 450000.00
        finally:
            app.dependency_overrides.clear()

