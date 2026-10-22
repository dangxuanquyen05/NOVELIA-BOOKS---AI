"""Novelia AI Assistant API endpoints: Chat, Conversation history, and Health diagnostic."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    get_current_user_optional,
    get_db,
    require_roles,
)
from app.models.user import User
from app.schemas.ai import (
    AIChatRequest,
    AIChatResponse,
    AIConfirmRequest,
    AIConfirmResponse,
    AIConversationRead,
    AIHealthResponse,
    AIMessageRead,
)
from app.services.ai_assistant_service import AIAssistantService

router = APIRouter(prefix="/ai", tags=["Novelia AI Assistant"])


@router.get(
    "/health",
    response_model=AIHealthResponse,
    summary="Kiểm tra trạng thái cấu hình và kết nối AI Provider",
)
def check_ai_health():
    """Verify whether AI Provider (Gemini / Mock) is configured and ready."""
    return AIAssistantService.get_health_status()


@router.post(
    "/chat",
    response_model=AIChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Gửi câu hỏi tới Novelia AI Assistant",
)
async def chat_with_assistant(
    payload: AIChatRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Interact with Novelia AI: catalog search, real-time stock, orders, and cart tools."""
    client_ip = request.client.host if request.client else "127.0.0.1"

    return await AIAssistantService.process_chat(
        db=db,
        message=payload.message,
        session_uuid=payload.session_uuid,
        current_user=current_user,
        client_ip=client_ip,
    )


@router.get(
    "/conversations",
    response_model=List[AIConversationRead],
    summary="Danh sách phiên hội thoại AI của người dùng",
)
def get_user_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve chat history sessions for the authenticated user."""
    return AIAssistantService.list_user_conversations(db, current_user.id)


@router.get(
    "/conversations/{session_uuid}",
    response_model=List[AIMessageRead],
    summary="Chi tiết lịch sử tin nhắn của một phiên hội thoại",
)
def get_conversation_history(
    session_uuid: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Retrieve turn-by-turn messages for a given session."""
    return AIAssistantService.get_conversation_messages(
        db=db,
        session_uuid=session_uuid,
        current_user=current_user,
    )


@router.post(
    "/confirm",
    response_model=AIConfirmResponse,
    status_code=status.HTTP_200_OK,
    summary="Xác nhận thực thi thao tác quản trị viên qua AI (Two-Phase Confirmation)",
)
def confirm_ai_action(
    payload: AIConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """Execute confirmed mutating AI action after re-validating preconditions."""
    return AIAssistantService.confirm_action(
        db=db,
        confirmation_token=payload.confirmation_token,
        staff_user=current_user,
    )

