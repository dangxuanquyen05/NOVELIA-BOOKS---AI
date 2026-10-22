"""Pydantic schemas for System Audit Logs and AI Action Traces."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AuditLogRead(BaseModel):
    """System-wide audit trail record."""

    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    """Paginated list of system audit logs."""

    items: List[AuditLogRead]
    total: int
    page: int
    limit: int


class AIActionLogRead(BaseModel):
    """AI tool execution audit record."""

    id: int
    conversation_id: Optional[int] = None
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    user_role: str
    tool_name: str
    input_arguments: Dict[str, Any]
    execution_status: str
    confirmation_token: Optional[str] = None
    is_confirmed: bool
    output_summary: Optional[str] = None
    execution_duration_ms: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIActionLogListResponse(BaseModel):
    """Paginated list of AI tool action logs."""

    items: List[AIActionLogRead]
    total: int
    page: int
    limit: int


class EmailStatusResponse(BaseModel):
    """Current email provider diagnostic status."""

    provider: str
    is_mock: bool
    status: str
    details: Dict[str, Any]
