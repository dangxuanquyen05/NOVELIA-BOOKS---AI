"""Pydantic schemas for Phase 7 Admin Dashboard, KPIs, and Governance."""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class DashboardKpiSummary(BaseModel):
    """Core financial and operational KPIs calculated authoritatively from MySQL."""

    total_revenue: Decimal = Field(..., description="Tổng doanh thu gộp từ các đơn hợp lệ (status != CANCELLED)")
    collected_revenue: Decimal = Field(..., description="Tổng tiền thực tế đã thu qua các cổng thanh toán (payment_status == PAID)")
    has_cost_data: bool = Field(False, description="Cờ xác nhận hệ thống có dữ liệu giá vốn nhập kho hay chưa")
    profit_note: str = Field(
        "Chưa có dữ liệu giá vốn nhập kho (COGS) để tính toán lợi nhuận ròng thực tế.",
        description="Ghi chú minh bạch về lợi nhuận tuân thủ nguyên tắc Truth in Financial Data"
    )
    total_orders: int = Field(..., description="Tổng số đơn hàng phát sinh trong kỳ")
    valid_orders_count: int = Field(..., description="Số đơn hàng thành công hoặc đang thực hiện (không tính đơn hủy)")
    average_order_value: Decimal = Field(..., description="Giá trị đơn trung bình (AOV)")
    total_books: int = Field(..., description="Tổng số đầu sách trong danh mục")
    low_stock_count: int = Field(..., description="Số đầu sách có tồn khả dụng <= ngưỡng cảnh báo")
    total_customers: int = Field(..., description="Tổng số tài khoản khách hàng")
    total_staff: int = Field(..., description="Tổng số nhân sự (Staff & Admin)")
    active_coupons_count: int = Field(..., description="Số mã giảm giá đang kích hoạt")


class RevenueTimelinePoint(BaseModel):
    """Daily / monthly timeline datapoint for trend visualization."""

    date_label: str = Field(..., description="Nhãn ngày (YYYY-MM-DD) hoặc tháng (YYYY-MM)")
    revenue: Decimal = Field(..., description="Doanh thu phát sinh")
    collected_cash: Decimal = Field(..., description="Tiền thực thu trong mốc này")
    order_count: int = Field(..., description="Số đơn hàng trong mốc này")


class OrderStatusCount(BaseModel):
    """Breakdown of orders by lifecycle status."""

    status: str
    label: str
    count: int
    percentage: float
    total_amount: Decimal


class TopSellingBook(BaseModel):
    """Top selling title performance."""

    book_id: int
    title: str
    isbn: str
    sku: Optional[str] = None
    cover_image_url: Optional[str] = None
    total_quantity_sold: int = 0
    units_sold: int = 0
    total_revenue: Decimal = Decimal("0.00")
    total_sales: Decimal = Decimal("0.00")
    current_stock: int = 0


class LowStockAlertItem(BaseModel):
    """Low stock warning details."""

    book_id: int
    title: str
    isbn: str
    sku: str
    physical_stock: int
    reserved_stock: int
    available_stock: int
    low_stock_threshold: int


class RecentActivityItem(BaseModel):
    """System event or transaction record."""

    id: str
    activity_type: str  # ORDER, INVENTORY, REVIEW, AUDIT
    title: str
    description: str
    created_at: datetime
    timestamp: Optional[datetime] = None
    badge_type: str = "info"
    severity: str = "info"


class AdminDashboardSummaryResponse(BaseModel):
    """Complete aggregated dashboard data response."""

    kpis: DashboardKpiSummary
    timeline: List[RevenueTimelinePoint]
    status_breakdown: List[OrderStatusCount]
    top_selling_books: List[TopSellingBook]
    low_stock_alerts: List[LowStockAlertItem]
    recent_activities: List[RecentActivityItem]
    filter_period: str


# ============================================================================
# CATEGORY / AUTHOR / PUBLISHER MANAGEMENT SCHEMAS
# ============================================================================

class AdminCategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = Field(None, max_length=255)
    parent_id: Optional[int] = None
    display_order: int = 0


class AdminCategoryUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    slug: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = Field(None, max_length=255)
    parent_id: Optional[int] = None
    display_order: Optional[int] = None


class AdminCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    display_order: int
    books_count: int = 0
    created_at: datetime


class AdminAuthorCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    slug: Optional[str] = Field(None, max_length=170)
    bio: Optional[str] = None
    avatar_url: Optional[str] = Field(None, max_length=500)
    birth_year: Optional[int] = None
    nationality: Optional[str] = Field(None, max_length=100)


class AdminAuthorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    birth_year: Optional[int] = None
    nationality: Optional[str] = None
    books_count: int = 0
    created_at: datetime


class AdminPublisherCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    slug: Optional[str] = Field(None, max_length=170)
    contact_info: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)


class AdminPublisherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    contact_info: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    books_count: int = 0
    created_at: datetime


# ============================================================================
# USER & PROMOTION GOVERNANCE SCHEMAS
# ============================================================================

class AdminUserItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    is_active: bool
    roles: List[str]
    orders_count: int = 0
    total_spent: Decimal = Decimal("0.00")
    created_at: datetime


class AdminUserListResponse(BaseModel):
    items: List[AdminUserItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminUserStatusUpdateRequest(BaseModel):
    is_active: bool = Field(..., description="Trạng thái kích hoạt tài khoản")


class AdminUserRoleUpdateRequest(BaseModel):
    roles: List[str] = Field(..., min_length=1, description="Danh sách roles gán cho user (CUSTOMER, STAFF, ADMIN)")


class AdminCouponCreateRequest(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    discount_type: str = Field("PERCENTAGE", description="PERCENTAGE hoặc FIXED_AMOUNT")
    discount_value: Decimal = Field(..., gt=0)
    min_order_value: Decimal = Field(Decimal("0.00"), ge=0)
    max_discount_value: Optional[Decimal] = Field(None, ge=0)
    usage_limit: Optional[int] = Field(None, ge=1)
    start_date: datetime
    end_date: datetime
    is_active: bool = True


class AdminCouponItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    description: Optional[str] = None
    discount_type: str
    discount_value: Decimal
    min_order_value: Decimal
    max_discount_value: Optional[Decimal] = None
    usage_limit: Optional[int] = None
    used_count: int
    start_date: datetime
    end_date: datetime
    is_active: bool
    total_discount_given: Decimal = Decimal("0.00")
    created_at: datetime
