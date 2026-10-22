"""Repository for system audit logging and AI action tracking with automated data sanitization."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.core.masking import mask_sensitive_data
from app.models.ai import AIActionLog
from app.models.audit import AuditLog
from app.models.user import User


class AuditRepository:
    """Data access layer for immutable audit trails and regulatory activity logging."""

    @staticmethod
    def record_audit(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[int] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Persist an immutable audit record with automatic sensitive data masking.

        Never records passwords, tokens, API keys, or CVVs in plaintext.
        """
        sanitized_old = mask_sensitive_data(old_values) if old_values else None
        sanitized_new = mask_sensitive_data(new_values) if new_values else None

        audit_entry = AuditLog(
            user_id=user_id,
            action=action.strip().upper(),
            entity_type=entity_type.strip().upper(),
            entity_id=str(entity_id) if entity_id is not None else None,
            old_values=sanitized_old,
            new_values=sanitized_new,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc),
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry

    @staticmethod
    def get_audit_logs(
        db: Session,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Query system audit logs with optional filters and user metadata."""
        query = db.query(AuditLog).options(joinedload(AuditLog.user))

        if action:
            query = query.filter(AuditLog.action == action.strip().upper())
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type.strip().upper())
        if entity_id:
            query = query.filter(AuditLog.entity_id == str(entity_id))
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        total_count = query.count()
        rows = (
            query.order_by(desc(AuditLog.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

        results = []
        for row in rows:
            user_email = row.user.email if row.user else None
            user_roles = [r.name for r in row.user.roles] if row.user and row.user.roles else []
            user_role = user_roles[0] if user_roles else None

            results.append({
                "id": row.id,
                "user_id": row.user_id,
                "user_email": user_email,
                "user_role": user_role,
                "action": row.action,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "old_values": row.old_values,
                "new_values": row.new_values,
                "ip_address": row.ip_address,
                "user_agent": row.user_agent,
                "created_at": row.created_at,
            })

        return results, total_count

    @staticmethod
    def get_ai_action_logs(
        db: Session,
        tool_name: Optional[str] = None,
        execution_status: Optional[str] = None,
        user_role: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Query AI tool action execution traces with caller user profile."""
        query = db.query(AIActionLog).options(joinedload(AIActionLog.user))

        if tool_name:
            query = query.filter(AIActionLog.tool_name == tool_name.strip())
        if execution_status:
            query = query.filter(
                AIActionLog.execution_status == execution_status.strip().upper()
            )
        if user_role:
            query = query.filter(AIActionLog.user_role == user_role.strip().upper())
        if user_id:
            query = query.filter(AIActionLog.user_id == user_id)

        total_count = query.count()
        rows = (
            query.order_by(desc(AIActionLog.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

        results = []
        for row in rows:
            user_email = row.user.email if row.user else None

            results.append({
                "id": row.id,
                "conversation_id": row.conversation_id,
                "user_id": row.user_id,
                "user_email": user_email,
                "user_role": row.user_role,
                "tool_name": row.tool_name,
                "input_arguments": row.input_arguments or {},
                "execution_status": row.execution_status,
                "confirmation_token": row.confirmation_token,
                "is_confirmed": row.is_confirmed,
                "output_summary": row.output_summary,
                "execution_duration_ms": row.execution_duration_ms,
                "created_at": row.created_at,
            })

        return results, total_count
