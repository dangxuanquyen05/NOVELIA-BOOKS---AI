"""API endpoints for Phase 8 Logistics, Shipping Providers, and Tracking Sync."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db, require_roles
from app.models.user import User
from app.schemas.shipping import (
    ShipmentDetailResponse,
    ShipmentDispatchCreateRequest,
    ShipmentTrackingLookupResponse,
    ShippingProviderStatusResponse,
)
from app.services.shipping_service import ShippingService

router = APIRouter(prefix="/shipping", tags=["Shipping & Logistics Operations"])


@router.post(
    "/orders/{order_code}/dispatch",
    response_model=ShipmentDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Dispatch order and create formal carrier shipment (STAFF/ADMIN)",
)
def dispatch_order(
    order_code: str,
    payload: ShipmentDispatchCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """Staff dispatches confirmed order to carrier (GHN, GHTK, or MOCK)."""
    return ShippingService.dispatch_order(
        db=db, order_code=order_code, payload=payload, current_user=current_user
    )


@router.get(
    "/orders/{order_code}/tracking",
    response_model=ShipmentDetailResponse,
    summary="Get order shipping status and tracking checkpoints (Customer or Staff)",
)
def get_order_tracking(
    order_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve full tracking timeline. Customer must own the order."""
    return ShippingService.get_order_tracking(
        db=db, order_code=order_code, current_user=current_user
    )


@router.get(
    "/track/{tracking_code}",
    response_model=ShipmentTrackingLookupResponse,
    summary="Public tracking lookup by carrier tracking code",
)
def lookup_tracking_code(
    tracking_code: str,
    db: Session = Depends(get_db),
):
    """Public tracking endpoint allowing readers to query parcel milestones."""
    return ShippingService.track_by_tracking_code(db=db, tracking_code=tracking_code)


@router.post(
    "/webhook/{carrier}",
    summary="Carrier webhook endpoint for status sync (GHN / GHTK / MOCK)",
)
async def carrier_webhook(
    carrier: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Receive and verify carrier status update webhooks."""
    try:
        raw_payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload webhook không phải định dạng JSON hợp lệ.",
        )

    # Pass all incoming headers to the adapter for signature/token validation
    headers_dict = dict(request.headers)
    return ShippingService.process_carrier_webhook(
        db=db, carrier=carrier, raw_payload=raw_payload, headers=headers_dict
    )


@router.post(
    "/orders/{order_code}/cancel-shipment",
    summary="Cancel shipping order with carrier (STAFF/ADMIN)",
)
def cancel_shipment(
    order_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """Staff cancels carrier dispatch before parcel is delivered."""
    return ShippingService.cancel_shipment(
        db=db, order_code=order_code, current_user=current_user
    )


@router.get(
    "/providers/status",
    response_model=List[ShippingProviderStatusResponse],
    summary="Get status of integrated shipping carriers (GHN, GHTK, MOCK)",
)
def get_providers_status(
    db: Session = Depends(get_db),
):
    """Check whether external shipping carriers are LIVE, SANDBOX, or BLOCKED."""
    return ShippingService.get_providers_status()
