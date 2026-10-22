"""Coupon and promotion database repository."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.commerce import Coupon, CouponUsage


class CouponRepository:
    """Data access layer for promotional discount vouchers."""

    @staticmethod
    def get_by_code(db: Session, code: str) -> Optional[Coupon]:
        return (
            db.query(Coupon)
            .filter(Coupon.code == code.strip().upper())
            .first()
        )

    @staticmethod
    def list_active(db: Session) -> List[Coupon]:
        """Fetch all currently active coupons within valid date range."""
        now = datetime.now(timezone.utc)
        return (
            db.query(Coupon)
            .filter(
                Coupon.is_active == True,
                Coupon.start_date <= now,
                Coupon.end_date >= now,
            )
            .order_by(Coupon.created_at.desc())
            .all()
        )

    @staticmethod
    def count_user_usage(db: Session, coupon_id: int, user_id: int) -> int:
        """Count how many times a user has redeemed this specific voucher."""
        return (
            db.query(CouponUsage)
            .filter(
                CouponUsage.coupon_id == coupon_id,
                CouponUsage.user_id == user_id,
            )
            .count()
        )

    @staticmethod
    def record_usage(
        db: Session,
        coupon: Coupon,
        user_id: int,
        order_id: int,
        discount_applied: Decimal,
    ) -> CouponUsage:
        """Increment used count and store usage audit record."""
        coupon.used_count += 1
        usage = CouponUsage(
            coupon_id=coupon.id,
            user_id=user_id,
            order_id=order_id,
            discount_applied=discount_applied,
            used_at=datetime.now(timezone.utc),
        )
        db.add(usage)
        db.flush()
        return usage

    @staticmethod
    def rollback_usage(db: Session, coupon_id: int, order_id: int) -> None:
        """Revert coupon redemption upon order cancellation."""
        usage = (
            db.query(CouponUsage)
            .filter(
                CouponUsage.coupon_id == coupon_id,
                CouponUsage.order_id == order_id,
            )
            .first()
        )
        if usage:
            coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
            if coupon and coupon.used_count > 0:
                coupon.used_count -= 1
            db.delete(usage)
            db.flush()
