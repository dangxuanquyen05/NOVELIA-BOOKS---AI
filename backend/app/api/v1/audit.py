"""Audit endpoints for viewing system operation logs, AI action traces, and email diagnostics."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.user import User
from app.schemas.audit import (
    AIActionLogListResponse,
    AuditLogListResponse,
    EmailStatusResponse,
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit & Governance"])


@router.get(
    "/logs",
    response_model=AuditLogListResponse,
    summary="List system audit logs (STAFF/ADMIN only)",
)
def get_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action name"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (ORDER, BOOK, INVENTORY)"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    user_id: Optional[int] = Query(None, description="Filter by operator user ID"),
    start_date: Optional[datetime] = Query(None, description="Start date ISO string"),
    end_date: Optional[datetime] = Query(None, description="End date ISO string"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """Retrieve immutable audit trails of sensitive business and administrative actions."""
    return AuditService.get_audit_trail(
        db=db,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit,
    )


@router.get(
    "/ai-actions",
    response_model=AIActionLogListResponse,
    summary="List AI tool execution traces (STAFF/ADMIN only)",
)
def get_ai_action_logs(
    tool_name: Optional[str] = Query(None, description="Filter by tool name"),
    execution_status: Optional[str] = Query(None, description="Filter by status (SUCCESS, REJECTED_RBAC, CONFIRMATION_REQUIRED)"),
    user_role: Optional[str] = Query(None, description="Filter by caller role"),
    user_id: Optional[int] = Query(None, description="Filter by caller user ID"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """Retrieve persistent AI execution and security audit logs."""
    return AuditService.get_ai_action_trail(
        db=db,
        tool_name=tool_name,
        execution_status=execution_status,
        user_role=user_role,
        user_id=user_id,
        page=page,
        limit=limit,
    )


@router.get(
    "/email-status",
    response_model=EmailStatusResponse,
    summary="Check active email delivery provider status (STAFF/ADMIN only)",
)
def get_email_status(
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """Inspect active email provider and verify whether delivery is Mock or Live SMTP."""
    return AuditService.get_email_status()
