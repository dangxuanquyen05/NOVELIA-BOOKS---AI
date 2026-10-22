"""Coupons and promotional voucher API endpoints."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional, get_db
from app.models.user import User
from app.repositories.coupon_repo import CouponRepository
from app.schemas.order import (
    CouponRead,
    CouponValidateRequest,
    CouponValidationResult,
)
from app.services.order_service import OrderService

router = APIRouter(prefix="/coupons", tags=["Coupons & Promotions"])


@router.post(
    "/validate",
    response_model=CouponValidationResult,
    summary="Kiểm tra tính hợp lệ của mã giảm giá",
)
def validate_coupon_code(
    payload: CouponValidateRequest,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Validate voucher against subtotal and customer redemption history."""
    user_id = current_user.id if current_user else None
    return OrderService.validate_coupon(
        db, payload.code, user_id, payload.cart_subtotal
    )


@router.get(
    "/active",
    response_model=List[CouponRead],
    summary="Danh sách voucher khuyến mãi đang kích hoạt",
)
def list_active_coupons(
    db: Session = Depends(get_db),
):
    """Retrieve public list of currently active coupons."""
    return CouponRepository.list_active(db)
