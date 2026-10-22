"""Order management and checkout API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.commerce import Order
from app.models.user import User
from app.repositories.order_repo import OrderRepository
from app.schemas.order import (
    CheckoutRequest,
    OrderCancelRequest,
    OrderRead,
    OrderStatusUpdateRequest,
    PaginatedOrdersResponse,
)
from app.services.order_service import OrderService

router = APIRouter(tags=["Orders & Checkout"])


def _format_order_response(order, payment_url: Optional[str] = None) -> OrderRead:
    res = OrderRead.model_validate(order)
    res.payment_method = order.payment.payment_method if order.payment else None
    res.payment_status = order.payment.payment_status if order.payment else None
    res.payment_url = payment_url
    if getattr(order, "shipment", None):
        res.shipment_carrier = order.shipment.carrier
        res.shipment_tracking_code = order.shipment.tracking_code
        res.shipment_status = order.shipment.status
    return res


@router.post(
    "/orders/checkout",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Thực hiện đặt hàng (Checkout)",
)
def checkout_order(
    payload: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Atomic order checkout enforcing backend pricing authority, stock locking, and coupon rules."""
    order, intent = OrderService.checkout(db, current_user, payload)
    return _format_order_response(order, payment_url=intent.get("payment_url"))


@router.get(
    "/orders",
    response_model=PaginatedOrdersResponse,
    summary="Danh sách đơn hàng của tôi",
)
def get_my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve customer's own order history with isolation."""
    items, total = OrderRepository.list_user_orders(
        db, current_user.id, page=page, page_size=page_size, status=status
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    orders_read = [_format_order_response(order) for order in items]

    return PaginatedOrdersResponse(
        items=orders_read,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/orders/{order_code}",
    response_model=OrderRead,
    summary="Chi tiết đơn hàng",
)
def get_order_detail(
    order_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve single order detail enforcing customer isolation unless staff."""
    is_staff = any(r in ["STAFF", "ADMIN"] for r in current_user.roles)
    user_id = None if is_staff else current_user.id

    order = OrderRepository.get_by_code(db, order_code, user_id=user_id)
    if not order:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy đơn hàng '{order_code}'.",
        )

    return _format_order_response(order)


@router.post(
    "/orders/{order_code}/cancel",
    response_model=OrderRead,
    summary="Hủy đơn hàng",
)
def cancel_order(
    order_code: str,
    payload: OrderCancelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel order and release reserved stock back into inventory."""
    order = OrderService.cancel_order(db, current_user, order_code, payload.reason)
    return _format_order_response(order)


# ============================================================================
# STAFF & ADMIN ORDER MANAGEMENT
# ============================================================================

@router.get(
    "/admin/orders",
    response_model=PaginatedOrdersResponse,
    summary="Quản trị đơn hàng toàn sàn (Staff & Admin)",
)
def admin_list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    current_user: User = Depends(require_roles(["STAFF", "ADMIN"])),
    db: Session = Depends(get_db),
):
    """List all store orders across all users with filters and search."""
    items, total = OrderRepository.list_all_orders(
        db, page=page, page_size=page_size, status=status, query=query
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    orders_read = [_format_order_response(order) for order in items]

    return PaginatedOrdersResponse(
        items=orders_read,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.put(
    "/admin/orders/{order_code}/status",
    response_model=OrderRead,
    summary="Cập nhật trạng thái đơn hàng (Staff & Admin)",
)
def admin_update_order_status(
    order_code: str,
    payload: OrderStatusUpdateRequest,
    current_user: User = Depends(require_roles(["STAFF", "ADMIN"])),
    db: Session = Depends(get_db),
):
    """Transition order status through fulfillment lifecycle."""
    order = OrderService.update_order_status(
        db=db,
        staff_user=current_user,
        order_code=order_code,
        new_status=payload.status,
        staff_notes=payload.staff_notes,
        cancellation_reason=payload.cancellation_reason,
    )
    return _format_order_response(order)
