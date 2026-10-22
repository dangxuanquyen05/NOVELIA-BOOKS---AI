"""Pydantic schemas for Novelia AI chat sessions, payloads, and audit trails."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AIChatRequest(BaseModel):
    """User prompt payload sent to Novelia AI."""

    message: str = Field(..., min_length=1, max_length=1000, description="Nội dung câu hỏi của người dùng")
    session_uuid: Optional[str] = Field(None, description="Mã phiên hội thoại (nếu đã có)")


class AIMessageRead(BaseModel):
    """Schema representing an individual dialogue turn."""

    id: Optional[int] = None
    sender: str
    content: str
    tool_calls: Optional[Any] = None
    tool_results: Optional[Any] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIChatResponse(BaseModel):
    """Structured assistant response delivered to client UI."""

    session_uuid: str
    message: str
    suggested_prompts: List[str] = Field(default_factory=list)
    structured_payload: Optional[Dict[str, Any]] = None
    created_at: datetime


class AIConversationRead(BaseModel):
    """Summary of a user conversation session."""

    id: int
    session_uuid: str
    title: Optional[str] = None
    conversation_type: str = "ASSISTANT"
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIHealthResponse(BaseModel):
    """Diagnostic AI health report."""

    status: str
    provider: str
    model: str
    is_configured: bool
    details: str


class AIConfirmRequest(BaseModel):
    """Payload to confirm an action requiring Two-Phase Confirmation."""

    confirmation_token: str = Field(..., description="Mã xác thực tạm thời của thao tác")


class AIConfirmResponse(BaseModel):
    """Result of executed confirmed mutation."""

    success: bool
    action_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    executed_at: datetime
