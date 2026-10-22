"""Inventory management API routes for staff and administration."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.database.connection import get_db
from app.models.user import User
from app.schemas.inventory import (
    InventoryAdjustmentRequest,
    InventoryInboundRequest,
    InventoryRead,
    InventoryTransactionRead,
    PaginatedInventoryResponse,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory Management & Stock Auditing"])


@router.get(
    "",
    response_model=PaginatedInventoryResponse,
    summary="List all inventory items with search and low-stock filter (Staff & Admin)",
)
def list_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    query: Optional[str] = Query(None, description="Search title, ISBN, SKU"),
    low_stock_only: bool = Query(False, description="Filter only items at or below safety threshold"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    return InventoryService.get_inventory(
        db,
        page=page,
        page_size=page_size,
        query=query,
        low_stock_only=low_stock_only,
    )


@router.get(
    "/low-stock",
    response_model=List[InventoryRead],
    summary="Get immediate alerts for low stock items (Staff & Admin)",
)
def get_low_stock_alerts(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    return InventoryService.get_low_stock_items(db, limit=limit)


@router.get(
    "/{book_id}/history",
    response_model=List[InventoryTransactionRead],
    summary="Get complete transaction audit trail for a book's inventory (Staff & Admin)",
)
def get_inventory_history(
    book_id: int,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    return InventoryService.get_history(db, book_id=book_id, limit=limit)


@router.post(
    "/inbound",
    response_model=InventoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Process inbound stock restock (Staff & Admin)",
)
def inbound_restock(
    data: InventoryInboundRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    return InventoryService.inbound_restock(db, data, staff_user=current_user)


@router.post(
    "/adjust",
    response_model=InventoryRead,
    summary="Manual stock adjustment with mandatory audit explanation (Staff & Admin)",
)
def adjust_stock(
    data: InventoryAdjustmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    return InventoryService.adjust_stock(db, data, staff_user=current_user)
