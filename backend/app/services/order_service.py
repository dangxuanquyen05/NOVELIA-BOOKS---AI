"""Order and Checkout processing service.

Enforces absolute backend authority over prices, coupons, and inventory with ACID transactions,
pessimistic locking, idempotent callbacks, and multi-tenant authorization.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.integrations.payment.factory import get_payment_provider
from app.models.catalog import Book
from app.models.commerce import Cart, CartItem, Order, OrderItem
from app.models.inventory import Inventory, InventoryTransaction
from app.models.payment_shipping import Payment
from app.models.user import User
from app.repositories.commerce_repo import CartRepository
from app.repositories.coupon_repo import CouponRepository
from app.repositories.order_repo import OrderRepository
from app.schemas.order import (
    CheckoutRequest,
    CouponValidationResult,
    OrderRead,
)


class OrderService:
    """Core domain logic for Checkout, Inventory Allocation, and Order Lifecycle."""

    @staticmethod
    def validate_coupon(
        db: Session,
        code: str,
        user_id: Optional[int] = None,
        cart_subtotal: Optional[Decimal] = None,
    ) -> CouponValidationResult:
        """Validate promotional voucher rules against subtotal and user history."""
        coupon = CouponRepository.get_by_code(db, code)
        if not coupon or not coupon.is_active:
            return CouponValidationResult(
                is_valid=False,
                code=code,
                message="Mã giảm giá không tồn tại hoặc đã ngừng kích hoạt.",
            )

        now = datetime.now(timezone.utc)
        if coupon.start_date > now:
            return CouponValidationResult(
                is_valid=False,
                code=code,
                message="Mã giảm giá chưa đến thời gian áp dụng.",
            )

        if coupon.end_date < now:
            return CouponValidationResult(
                is_valid=False,
                code=code,
                message="Mã giảm giá đã hết hạn sử dụng.",
            )

        if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
            return CouponValidationResult(
                is_valid=False,
                code=code,
                message="Mã giảm giá đã hết lượt sử dụng trên hệ thống.",
            )

        if cart_subtotal is not None and cart_subtotal < coupon.min_order_value:
            return CouponValidationResult(
                is_valid=False,
                code=code,
                min_order_value=coupon.min_order_value,
                message=f"Đơn hàng phải đạt tối thiểu {float(coupon.min_order_value):,.0f} VND để áp dụng mã này.",
            )

        if user_id is not None:
            usage_count = CouponRepository.count_user_usage(db, coupon.id, user_id)
            if usage_count >= 1:
                return CouponValidationResult(
                    is_valid=False,
                    code=code,
                    message="Bạn đã sử dụng mã giảm giá này cho một đơn hàng trước đó.",
                )

        # Calculate estimated discount
        discount_amount = Decimal("0.00")
        if cart_subtotal is not None:
            if coupon.discount_type == "PERCENTAGE":
                raw = (cart_subtotal * coupon.discount_value) / Decimal("100.00")
                if coupon.max_discount_value is not None:
                    discount_amount = min(raw, coupon.max_discount_value)
                else:
                    discount_amount = raw
            else:
                discount_amount = min(cart_subtotal, coupon.discount_value)

        return CouponValidationResult(
            is_valid=True,
            code=coupon.code,
            discount_type=coupon.discount_type,
            discount_value=coupon.discount_value,
            discount_amount=discount_amount.quantize(Decimal("0.01")),
            min_order_value=coupon.min_order_value,
            message=f"Áp dụng thành công mã {coupon.code}.",
        )

    @classmethod
    def checkout(
        cls,
        db: Session,
        user: User,
        data: CheckoutRequest,
    ) -> Tuple[Order, dict]:
        """Execute atomic checkout with pessimistic inventory locking."""
        # 1. Idempotency Check: Prevent duplicate order submission
        if data.idempotency_key:
            existing = OrderRepository.find_by_idempotency_key(
                db, user.id, data.idempotency_key
            )
            if existing:
                provider = get_payment_provider(existing.payment.payment_method)
                intent = provider.create_payment_intent(existing, existing.payment)
                return existing, intent

        # 2. Retrieve active Cart items
        cart = CartRepository.get_or_create(db, user.id)
        if not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Giỏ hàng của bạn đang trống. Vui lòng chọn sách trước khi đặt hàng.",
            )

        # 3. Sort items by book_id to enforce consistent lock ordering (Deadlock prevention)
        sorted_cart_items = sorted(cart.items, key=lambda x: x.book_id)

        # 4. Pessimistic Locking & Stock Verification
        subtotal_amount = Decimal("0.00")
        order_items_to_create: List[OrderItem] = []

        for item in sorted_cart_items:
            # SELECT ... FOR UPDATE locks the inventory row until commit
            inv = (
                db.query(Inventory)
                .filter(Inventory.book_id == item.book_id)
                .with_for_update()
                .first()
            )
            if not inv:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Tác phẩm ID {item.book_id} không có dữ liệu tồn kho.",
                )

            available = inv.physical_stock - inv.reserved_stock
            if available < item.quantity:
                book_name = item.book.title if item.book else f"ID {item.book_id}"
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Tác phẩm '{book_name}' chỉ còn {available} cuốn khả dụng, "
                        f"không đủ số lượng yêu cầu ({item.quantity} cuốn)."
                    ),
                )

            # Re-fetch authoritative book data from database (Zero trust in client prices)
            book = db.query(Book).filter(Book.id == item.book_id).first()
            if not book or book.status != "ACTIVE":
                book_name = book.title if book else f"ID {item.book_id}"
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Tác phẩm '{book_name}' hiện tạm ngừng kinh doanh.",
                )

            book_price = Decimal(str(book.price))
            item_subtotal = book_price * Decimal(str(item.quantity))
            subtotal_amount += item_subtotal

            # Reserve stock
            inv.reserved_stock += item.quantity

            # Prepare permanent line item snapshot
            order_item = OrderItem(
                book_id=book.id,
                book_title_snapshot=book.title,
                book_isbn_snapshot=book.isbn,
                book_sku_snapshot=book.sku,
                price_at_purchase=book_price,
                quantity=item.quantity,
                subtotal=item_subtotal,
                created_at=datetime.now(timezone.utc),
            )
            order_items_to_create.append(order_item)

        # 5. Shipping Fee Calculation (Authoritative backend calculation)
        # Free shipping on orders >= 500,000 VND; otherwise standard flat rate 30,000 VND
        shipping_fee = (
            Decimal("0.00")
            if subtotal_amount >= Decimal("500000.00")
            else Decimal("30000.00")
        )

        # 6. Promo Code / Coupon Validation
        discount_amount = Decimal("0.00")
        coupon = None
        if data.coupon_code and data.coupon_code.strip():
            c_val = cls.validate_coupon(
                db, data.coupon_code.strip(), user.id, subtotal_amount
            )
            if not c_val.is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=c_val.message,
                )
            discount_amount = c_val.discount_amount
            coupon = CouponRepository.get_by_code(db, data.coupon_code.strip())

        # 7. Final Order Total
        total_amount = max(
            Decimal("0.00"), subtotal_amount + shipping_fee - discount_amount
        ).quantize(Decimal("0.01"))

        # 8. Unique Order & Payment Codes
        timestamp_prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
        random_suffix = uuid.uuid4().hex[:6].upper()
        order_code = f"NVL-{timestamp_prefix}-{random_suffix}"
        payment_code = f"PAY-{uuid.uuid4().hex[:8].upper()}"

        payment_method = data.payment_method.strip().upper()
        initial_order_status = "CONFIRMED" if payment_method == "COD" else "PENDING"

        order = Order(
            order_code=order_code,
            user_id=user.id,
            subtotal_amount=subtotal_amount.quantize(Decimal("0.01")),
            shipping_fee=shipping_fee.quantize(Decimal("0.01")),
            discount_amount=discount_amount.quantize(Decimal("0.01")),
            total_amount=total_amount,
            status=initial_order_status,
            recipient_name=data.recipient_name.strip(),
            recipient_phone=data.recipient_phone.strip(),
            shipping_province=data.shipping_province.strip(),
            shipping_district=data.shipping_district.strip(),
            shipping_ward=data.shipping_ward.strip(),
            shipping_street_address=data.shipping_street_address.strip(),
            shipping_formatted_address=data.shipping_formatted_address.strip() if data.shipping_formatted_address else None,
            shipping_latitude=data.shipping_latitude,
            shipping_longitude=data.shipping_longitude,
            customer_notes=data.customer_notes.strip() if data.customer_notes else None,
            staff_notes=(
                f"IDEMPOTENCY:{data.idempotency_key}"
                if data.idempotency_key
                else None
            ),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        payment = Payment(
            payment_code=payment_code,
            payment_method=payment_method,
            payment_status="PENDING",
            amount=total_amount,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # 9. Persist Order and Items
        OrderRepository.create_order(db, order, order_items_to_create, payment)

        # 10. Record Inventory Transaction Audit Trails
        for item in sorted_cart_items:
            inv = (
                db.query(Inventory).filter(Inventory.book_id == item.book_id).first()
            )
            tx = InventoryTransaction(
                inventory_id=inv.id,
                transaction_type="ORDER_RESERVED",
                quantity_change=item.quantity,
                stock_after=inv.physical_stock,
                reference_code=order.order_code,
                notes=f"Khóa giữ hàng cho đơn {order.order_code}",
                created_by_user_id=user.id,
                created_at=datetime.now(timezone.utc),
            )
            db.add(tx)

        # 11. Record Coupon Usage
        if coupon and discount_amount > 0:
            CouponRepository.record_usage(
                db, coupon, user.id, order.id, discount_amount
            )

        # 12. Clear User's Cart
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()

        # 13. Initialize Payment Gateway Intent
        provider = get_payment_provider(payment_method)
        intent = provider.create_payment_intent(order, payment)

        # 14. Commit ACID transaction
        db.commit()
        db.refresh(order)

        # 15. Trigger In-App Notification, Order Confirmation Email, and Audit Record
        try:
            from app.repositories.notification_repo import NotificationRepository
            from app.services.email_service import EmailService
            from app.repositories.audit_repo import AuditRepository

            NotificationRepository.create_notification(
                db=db,
                user_id=user.id,
                title=f"Đặt hàng thành công #{order.order_code}",
                message=f"Đơn hàng {order.order_code} của bạn đã được tiếp nhận với tổng thanh toán {int(order.final_amount):,} VND.",
                notification_type="ORDER",
                reference_link=f"/orders/{order.order_code}",
            )
            if user.email:
                EmailService.send_order_confirmation_email(order, user.email)

            AuditRepository.record_audit(
                db=db,
                action="ORDER_CREATED",
                entity_type="ORDER",
                entity_id=order.order_code,
                user_id=user.id,
                new_values={
                    "final_amount": str(order.final_amount),
                    "items_count": len(order.items),
                    "payment_method": order.payment.payment_method if order.payment else "COD",
                },
            )
        except Exception:
            # Non-negotiable rule: Email/notification failures must NEVER corrupt order creation
            pass

        return order, intent

    @classmethod
    def cancel_order(
        cls,
        db: Session,
        user: User,
        order_code: str,
        reason: str,
    ) -> Order:
        """Cancel an order and release reserved inventory back to availability."""
        order = OrderRepository.get_by_code(db, order_code)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy đơn hàng {order_code}.",
            )

        # Check tenant isolation & authorization
        is_staff_or_admin = any(r in ["STAFF", "ADMIN"] for r in user.roles)
        if not is_staff_or_admin and order.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền thao tác trên đơn hàng của người khác.",
            )

        # Order Cancellation Policy (ADR-004 & AGENTS.md):
        # Customers can ONLY cancel when status is PENDING
        if not is_staff_or_admin and order.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Khách hàng chỉ có thể hủy đơn khi ở trạng thái Chờ xử lý (PENDING).",
            )

        # Staff can cancel PENDING or CONFIRMED orders
        if order.status not in ["PENDING", "CONFIRMED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Đơn hàng ở trạng thái '{order.status}' không thể hủy bỏ.",
            )

        # Release reserved inventory
        for item in order.items:
            if item.book_id:
                inv = (
                    db.query(Inventory)
                    .filter(Inventory.book_id == item.book_id)
                    .with_for_update()
                    .first()
                )
                if inv:
                    inv.reserved_stock = max(0, inv.reserved_stock - item.quantity)
                    tx = InventoryTransaction(
                        inventory_id=inv.id,
                        transaction_type="ORDER_CANCELLED",
                        quantity_change=-item.quantity,
                        stock_after=inv.physical_stock,
                        reference_code=order.order_code,
                        notes=f"Hủy đơn {order.order_code}: {reason.strip()}",
                        created_by_user_id=user.id,
                        created_at=datetime.now(timezone.utc),
                    )
                    db.add(tx)

        # Rollback coupon redemptions if any
        if order.coupon_usages:
            for usage in order.coupon_usages:
                CouponRepository.rollback_usage(db, usage.coupon_id, order.id)

        # Update order status
        OrderRepository.update_order_status(
            db,
            order=order,
            new_status="CANCELLED",
            staff_notes=f"Hủy bởi {user.full_name} ({user.email})",
            cancelled_reason=reason.strip(),
        )

        # Update payment status
        if order.payment:
            if order.payment.payment_status == "PAID":
                order.payment.payment_status = "REFUNDED"
            else:
                order.payment.payment_status = "CANCELLED"
            order.payment.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(order)

        # Trigger notification and audit logging for cancellation
        try:
            from app.services.notification_service import NotificationService
            from app.repositories.audit_repo import AuditRepository

            NotificationService.notify_order_status_change(
                db, order=order, old_status="PENDING", new_status="CANCELLED", notes=reason.strip()
            )
            AuditRepository.record_audit(
                db=db,
                action="ORDER_CANCELLED",
                entity_type="ORDER",
                entity_id=order.order_code,
                user_id=user.id,
                old_values={"status": "PENDING"},
                new_values={"status": "CANCELLED", "reason": reason.strip()},
            )
        except Exception:
            pass

        return order

    @classmethod
    def update_order_status(
        cls,
        db: Session,
        staff_user: User,
        order_code: str,
        new_status: str,
        staff_notes: Optional[str] = None,
        cancellation_reason: Optional[str] = None,
    ) -> Order:
        """Staff/Admin lifecycle status progression."""
        order = OrderRepository.get_by_code(db, order_code)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy đơn hàng {order_code}.",
            )

        old_status = order.status

        valid_statuses = [
            "PENDING",
            "CONFIRMED",
            "PROCESSING",
            "SHIPPING",
            "COMPLETED",
            "CANCELLED",
        ]
        target = new_status.strip().upper()
        if target not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Trạng thái '{new_status}' không hợp lệ.",
            )

        if target == "CANCELLED":
            if not cancellation_reason:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bắt buộc phải nhập lý do khi hủy đơn hàng.",
                )
            return cls.cancel_order(db, staff_user, order_code, cancellation_reason)

        # When transitioning to SHIPPING: stock moves from reserved out of warehouse (deduct physical_stock)
        if target == "SHIPPING" and order.status in ["CONFIRMED", "PROCESSING"]:
            for item in order.items:
                if item.book_id:
                    inv = (
                        db.query(Inventory)
                        .filter(Inventory.book_id == item.book_id)
                        .with_for_update()
                        .first()
                    )
                    if inv:
                        inv.physical_stock = max(0, inv.physical_stock - item.quantity)
                        inv.reserved_stock = max(0, inv.reserved_stock - item.quantity)
                        tx = InventoryTransaction(
                            inventory_id=inv.id,
                            transaction_type="ORDER_SHIPPED",
                            quantity_change=-item.quantity,
                            stock_after=inv.physical_stock,
                            reference_code=order.order_code,
                            notes=f"Xuất kho giao hàng đơn {order.order_code}",
                            created_by_user_id=staff_user.id,
                            created_at=datetime.now(timezone.utc),
                        )
                        db.add(tx)

        OrderRepository.update_order_status(
            db,
            order=order,
            new_status=target,
            staff_notes=staff_notes,
        )

        db.commit()
        db.refresh(order)

        # Trigger notification and audit logging for status progression
        try:
            from app.services.notification_service import NotificationService
            from app.repositories.audit_repo import AuditRepository

            NotificationService.notify_order_status_change(
                db, order=order, old_status=old_status, new_status=target, notes=staff_notes
            )
            AuditRepository.record_audit(
                db=db,
                action="ORDER_STATUS_UPDATE",
                entity_type="ORDER",
                entity_id=order.order_code,
                user_id=staff_user.id,
                old_values={"status": old_status},
                new_values={"status": target, "staff_notes": staff_notes},
            )
        except Exception:
            pass

        return order

    @classmethod
    def process_gateway_webhook(
        cls,
        db: Session,
        gateway: str,
        payload: dict,
        signature: str,
    ) -> dict:
        """Process gateway payment callback with cryptographic verification and replay protection."""
        provider = get_payment_provider(gateway)

        # 1. Cryptographic Signature Verification
        if not provider.verify_webhook_signature(payload, signature):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chữ ký xác thực cổng thanh toán không hợp lệ.",
            )

        # 2. Extract parsed callback parameters
        parsed = provider.process_callback(payload)
        order_code = parsed["order_code"]

        order = OrderRepository.get_by_code(db, order_code)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy đơn hàng {order_code} trong callback.",
            )

        payment = order.payment
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Đơn hàng chưa được khởi tạo bản ghi thanh toán.",
            )

        # 3. Idempotent Handling / Replay Protection
        # If already marked PAID, return success immediately without modifying state
        if payment.payment_status == "PAID":
            return {
                "status": "already_paid",
                "order_code": order_code,
                "message": "Giao dịch đã được ghi nhận thanh toán trước đó.",
            }

        # 4. Mark payment outcome
        if parsed["is_success"]:
            payment.payment_status = "PAID"
            payment.paid_at = datetime.now(timezone.utc)
            payment.transaction_id = parsed["transaction_id"]
            payment.gateway_response = payload
            payment.updated_at = datetime.now(timezone.utc)

            # Auto-confirm order if pending
            if order.status == "PENDING":
                order.status = "CONFIRMED"
                order.updated_at = datetime.now(timezone.utc)
        else:
            payment.payment_status = "FAILED"
            payment.gateway_response = payload
            payment.updated_at = datetime.now(timezone.utc)

        db.commit()
        return {
            "status": "success" if parsed["is_success"] else "failed",
            "order_code": order_code,
            "message": parsed["message"],
        }
