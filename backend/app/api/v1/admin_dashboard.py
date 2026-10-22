"""API endpoints for Phase 7 Admin Dashboard, KPIs, and Store Governance."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.database.connection import get_db
from app.models.user import User
from app.schemas.admin_dashboard import (
    AdminAuthorCreateRequest,
    AdminAuthorResponse,
    AdminCategoryCreateRequest,
    AdminCategoryResponse,
    AdminCategoryUpdateRequest,
    AdminCouponCreateRequest,
    AdminCouponItem,
    AdminDashboardSummaryResponse,
    AdminPublisherCreateRequest,
    AdminPublisherResponse,
    AdminUserItem,
    AdminUserListResponse,
    AdminUserRoleUpdateRequest,
    AdminUserStatusUpdateRequest,
)
from app.services.admin_dashboard_service import AdminDashboardService

router = APIRouter(prefix="/admin/dashboard", tags=["Admin Dashboard & Store Operations"])


# =============================================================================
# EXECUTIVE DASHBOARD & KPIS
# =============================================================================

@router.get(
    "/summary",
    response_model=AdminDashboardSummaryResponse,
    summary="Get executive dashboard summary metrics, timelines, and status breakdown",
)
def get_dashboard_summary(
    period: str = Query("30days", description="Time window: 7days, 30days, 90days, 12months, all"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """Retrieve full dashboard performance statistics, revenue, AOV, best-sellers, and low stock."""
    return AdminDashboardService.get_dashboard_summary(db, period=period)


# =============================================================================
# CATEGORIES MANAGEMENT
# =============================================================================

@router.get(
    "/categories",
    response_model=List[AdminCategoryResponse],
    summary="List all categories with associated books count",
)
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """List store categories including book count."""
    return AdminDashboardService.list_categories(db)


@router.post(
    "/categories",
    response_model=AdminCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new book category",
)
def create_category(
    payload: AdminCategoryCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """Create category taxonomy."""
    return AdminDashboardService.create_category(db, payload)


@router.put(
    "/categories/{category_id}",
    response_model=AdminCategoryResponse,
    summary="Update category details",
)
def update_category(
    category_id: int,
    payload: AdminCategoryUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """Update existing category taxonomy."""
    return AdminDashboardService.update_category(db, category_id, payload)


@router.delete(
    "/categories/{category_id}",
    summary="Delete category if no books are attached",
)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """Delete an empty category taxonomy."""
    return AdminDashboardService.delete_category(db, category_id)


# =============================================================================
# AUTHORS & PUBLISHERS MANAGEMENT
# =============================================================================

@router.get(
    "/authors",
    response_model=List[AdminAuthorResponse],
    summary="List authors with book counts",
)
def list_authors(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """List all registered authors and their title count."""
    return AdminDashboardService.list_authors(db)


@router.post(
    "/authors",
    response_model=AdminAuthorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new author profile",
)
def create_author(
    payload: AdminAuthorCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """Register author profile."""
    return AdminDashboardService.create_author(db, payload)


@router.get(
    "/publishers",
    response_model=List[AdminPublisherResponse],
    summary="List publishers with published book counts",
)
def list_publishers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """List all registered book publishers."""
    return AdminDashboardService.list_publishers(db)


@router.post(
    "/publishers",
    response_model=AdminPublisherResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new publisher profile",
)
def create_publisher(
    payload: AdminPublisherCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """Register publisher profile."""
    return AdminDashboardService.create_publisher(db, payload)


# =============================================================================
# USER GOVERNANCE (CUSTOMERS & STAFF - ADMIN ONLY)
# =============================================================================

@router.get(
    "/users",
    response_model=AdminUserListResponse,
    summary="List customers and staff with order history stats (ADMIN ONLY)",
)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[str] = Query(None, description="Filter by role: CUSTOMER, STAFF, ADMIN"),
    query: Optional[str] = Query(None, description="Search query by email, name, or phone"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    """List system users with aggregated order spending statistics."""
    return AdminDashboardService.list_users(
        db, page=page, page_size=page_size, role=role, query=query
    )


@router.put(
    "/users/{user_id}/status",
    response_model=AdminUserItem,
    summary="Toggle user active status (ADMIN ONLY)",
)
def set_user_status(
    user_id: int,
    payload: AdminUserStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    """Activate or deactivate user account."""
    return AdminDashboardService.set_user_status(
        db, current_admin=current_user, user_id=user_id, is_active=payload.is_active
    )


@router.put(
    "/users/{user_id}/role",
    response_model=AdminUserItem,
    summary="Update user roles (ADMIN ONLY)",
)
def set_user_roles(
    user_id: int,
    payload: AdminUserRoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    """Update assigned user roles."""
    return AdminDashboardService.set_user_roles(
        db, current_admin=current_user, user_id=user_id, roles=payload.roles
    )


# =============================================================================
# PROMOTIONS & COUPONS GOVERNANCE
# =============================================================================

@router.get(
    "/coupons",
    response_model=List[AdminCouponItem],
    summary="List all coupons with usage metrics",
)
def list_coupons(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """List discount coupons and their usage status."""
    return AdminDashboardService.list_coupons(db)


@router.post(
    "/coupons",
    response_model=AdminCouponItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new discount coupon",
)
def create_coupon(
    payload: AdminCouponCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """Create promotion code with limits and dates."""
    return AdminDashboardService.create_coupon(db, payload)


@router.put(
    "/coupons/{coupon_id}/toggle",
    response_model=AdminCouponItem,
    summary="Toggle active state of coupon",
)
def toggle_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """Toggle coupon active/inactive status."""
    return AdminDashboardService.toggle_coupon_status(db, coupon_id)
