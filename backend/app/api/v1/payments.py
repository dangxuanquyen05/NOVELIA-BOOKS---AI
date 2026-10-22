"""Payments API router for gateway webhooks and verification status."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.order_repo import OrderRepository
from app.schemas.payment import PaymentStatusResponse
from app.services.order_service import OrderService

router = APIRouter(prefix="/payments", tags=["Payments & Gateways"])


@router.post(
    "/webhook/{gateway}",
    summary="Webhook nhận phản hồi từ cổng thanh toán (IPN/Callback)",
)
async def payment_webhook(
    gateway: str,
    request: Request,
    db: Session = Depends(get_db),
    x_signature: str = Header(None, alias="X-Signature"),
):
    """Process incoming payment gateway webhook notification with signature verification.

    Protected against callback replays (idempotent handling).
    """
    try:
        payload = await request.json()
    except Exception:
        # Fallback to query params if gateway passes form/query params (e.g. VNPay return)
        payload = dict(request.query_params)

    # If signature not in header, look inside payload (e.g. vnp_SecureHash, signature)
    signature = (
        x_signature
        or payload.get("vnp_SecureHash")
        or payload.get("signature")
        or payload.get("sig")
        or ""
    )

    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Thiếu chữ ký xác thực cổng thanh toán (Signature missing).",
        )

    result = OrderService.process_gateway_webhook(
        db=db,
        gateway=gateway.strip().upper(),
        payload=payload,
        signature=str(signature),
    )
    return result


@router.get(
    "/{order_code}/status",
    response_model=PaymentStatusResponse,
    summary="Kiểm tra trạng thái thanh toán của đơn hàng",
)
def get_payment_status(
    order_code: str,
    db: Session = Depends(get_db),
):
    """Retrieve real-time payment status of an order."""
    order = OrderRepository.get_by_code(db, order_code)
    if not order or not order.payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy thông tin thanh toán cho đơn {order_code}.",
        )

    payment = order.payment
    return PaymentStatusResponse(
        order_code=order.order_code,
        payment_status=payment.payment_status,
        payment_method=payment.payment_method,
        amount=payment.amount,
        transaction_id=payment.transaction_id,
        paid_at=payment.paid_at,
    )
