"""Service layer for governance audit trails, AI copilot traces, and email diagnostics."""

from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.integrations.email.factory import get_email_provider
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.schemas.audit import (
    AIActionLogListResponse,
    AIActionLogRead,
    AuditLogListResponse,
    AuditLogRead,
    EmailStatusResponse,
)


class AuditService:
    """Orchestration service for regulatory audits and operational history."""

    @classmethod
    def record_action(
        cls,
        db: Session,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user: Optional[User] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLogRead:
        """Record a sensitive business operation with automatic PII and secret redaction."""
        user_id = user.id if user else None
        audit = AuditRepository.record_audit(
            db=db,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        user_email = user.email if user else None
        user_roles = [r.name for r in user.roles] if user and user.roles else []
        user_role = user_roles[0] if user_roles else None

        return AuditLogRead(
            id=audit.id,
            user_id=audit.user_id,
            user_email=user_email,
            user_role=user_role,
            action=audit.action,
            entity_type=audit.entity_type,
            entity_id=audit.entity_id,
            old_values=audit.old_values,
            new_values=audit.new_values,
            ip_address=audit.ip_address,
            user_agent=audit.user_agent,
            created_at=audit.created_at,
        )

    @classmethod
    def get_audit_trail(
        cls,
        db: Session,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        limit: int = 20,
    ) -> AuditLogListResponse:
        """Retrieve paginated audit logs for staff and administrators."""
        offset = max(0, (page - 1) * limit)
        items, total = AuditRepository.get_audit_logs(
            db=db,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

        return AuditLogListResponse(
            items=[AuditLogRead.model_validate(it) for it in items],
            total=total,
            page=page,
            limit=limit,
        )

    @classmethod
    def get_ai_action_trail(
        cls,
        db: Session,
        tool_name: Optional[str] = None,
        execution_status: Optional[str] = None,
        user_role: Optional[str] = None,
        user_id: Optional[int] = None,
        page: int = 1,
        limit: int = 20,
    ) -> AIActionLogListResponse:
        """Retrieve paginated AI tool execution history for auditing."""
        offset = max(0, (page - 1) * limit)
        items, total = AuditRepository.get_ai_action_logs(
            db=db,
            tool_name=tool_name,
            execution_status=execution_status,
            user_role=user_role,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

        return AIActionLogListResponse(
            items=[AIActionLogRead.model_validate(it) for it in items],
            total=total,
            page=page,
            limit=limit,
        )

    @classmethod
    def get_email_status(cls) -> EmailStatusResponse:
        """Inspect active email provider and delivery environment."""
        provider = get_email_provider()
        health = provider.check_health()
        return EmailStatusResponse(
            provider=health.get("provider", "UNKNOWN"),
            is_mock=health.get("is_mock", True),
            status=health.get("status", "HEALTHY"),
            details=health,
        )
