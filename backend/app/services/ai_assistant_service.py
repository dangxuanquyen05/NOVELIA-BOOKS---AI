"""Orchestration service for Novelia AI Assistant sessions, guardrails, and tool loops."""

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.integrations.ai.base import AIMessagePayload
from app.integrations.ai.factory import get_ai_provider
from app.integrations.ai.guardrails import AIGuardrails
from app.integrations.ai.tools import (
    ADMIN_TOOL_DEFINITIONS,
    CUSTOMER_TOOL_DEFINITIONS,
    AIToolExecutor,
)
from app.models.ai import AIActionLog, AIConversation, AIMessage
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.ai import (
    AIChatResponse,
    AIConfirmResponse,
    AIConversationRead,
    AIHealthResponse,
    AIMessageRead,
)


class AIAssistantService:
    """Manages conversational dialogue sessions, tool calling loops, and persistent auditing."""

    @classmethod
    def get_or_create_conversation(
        cls,
        db: Session,
        session_uuid: Optional[str] = None,
        current_user: Optional[User] = None,
    ) -> AIConversation:
        """Find existing session or initialize a new conversation."""
        conv: Optional[AIConversation] = None
        if session_uuid:
            conv = db.query(AIConversation).filter(AIConversation.session_uuid == session_uuid).first()

        if conv:
            # If user logged in during an anonymous session, link user_id
            if current_user and not conv.user_id:
                conv.user_id = current_user.id
                db.commit()
            return conv

        # Generate new session UUID
        new_uuid = session_uuid or f"nvl_conv_{uuid.uuid4().hex[:16]}"
        conv = AIConversation(
            session_uuid=new_uuid,
            user_id=current_user.id if current_user else None,
            conversation_type="ASSISTANT",
            title="Cuộc trò chuyện mới",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    @classmethod
    async def process_chat(
        cls,
        db: Session,
        message: str,
        session_uuid: Optional[str] = None,
        current_user: Optional[User] = None,
        client_ip: str = "127.0.0.1",
    ) -> AIChatResponse:
        """Orchestrate AI interaction, rate limit verification, tool execution, and audit trail."""
        # 1. Enforce Rate Limiting
        rate_key = f"user_{current_user.id}" if current_user else f"ip_{client_ip}"
        AIGuardrails.check_rate_limit(rate_key)

        # 2. Sanitize and Validate Prompt
        cleaned_prompt = AIGuardrails.validate_and_sanitize_prompt(message)

        # 3. Retrieve or create session
        conversation = cls.get_or_create_conversation(db, session_uuid, current_user)

        # 4. Save User Message
        user_msg = AIMessage(
            conversation_id=conversation.id,
            sender="USER",
            content=cleaned_prompt,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user_msg)
        db.commit()

        # Update conversation title if first message
        if conversation.title == "Cuộc trò chuyện mới":
            conversation.title = cleaned_prompt[:40] + ("..." if len(cleaned_prompt) > 40 else "")
            db.commit()

        # 4.1. Conversational Ordering Assistant (Direct Order Flow & Multi-turn state)
        from app.services.order_assistant_service import OrderAssistantService
        order_handled, order_reply, order_payload = OrderAssistantService.handle_order_conversation(
            db=db,
            message=cleaned_prompt,
            session_uuid=conversation.session_uuid,
            current_user=current_user,
        )
        if order_handled:
            tokens_est = max(1, (len(cleaned_prompt) + len(order_reply)) // 4)
            asst_msg = AIMessage(
                conversation_id=conversation.id,
                sender="ASSISTANT",
                content=order_reply,
                tokens_used=tokens_est,
                created_at=datetime.now(timezone.utc),
            )
            db.add(asst_msg)
            db.commit()

            return AIChatResponse(
                session_uuid=conversation.session_uuid,
                message=order_reply,
                suggested_prompts=["📦 Kiểm tra đơn hàng", "📚 Tìm sách khác", "Hủy"],
                structured_payload=order_payload or {},
                created_at=datetime.now(timezone.utc),
            )

        # 5. Resolve AI Provider and check health
        provider = get_ai_provider()
        health = provider.check_health()

        # Realism rule: If external provider is missing API key, provide intelligent rule-based fallback
        if health.status == "MISSING_API_KEY":
            from app.integrations.ai.fallback import get_fallback_response
            fallback_text, intent = get_fallback_response(
                db=db,
                message=cleaned_prompt,
                current_user=current_user,
            )
            asst_msg = AIMessage(
                conversation_id=conversation.id,
                sender="ASSISTANT",
                content=fallback_text,
                tokens_used=max(1, (len(cleaned_prompt) + len(fallback_text)) // 4),
                created_at=datetime.now(timezone.utc),
            )
            db.add(asst_msg)
            db.commit()

            return AIChatResponse(
                session_uuid=conversation.session_uuid,
                message=fallback_text,
                suggested_prompts=["Kiểm tra trạng thái hệ thống", "Tìm sách trên cửa hàng", "Phí vận chuyển"],
                structured_payload={"is_configured": False, "status": "MISSING_API_KEY", "is_fallback": True, "intent": intent},
                created_at=datetime.now(timezone.utc),
            )

        # 6. Assemble context messages from conversation history (prior turns)
        history_msgs = (
            db.query(AIMessage)
            .filter(AIMessage.conversation_id == conversation.id)
            .order_by(AIMessage.created_at.asc())
            .limit(10)
            .all()
        )

        payload_messages: List[AIMessagePayload] = []
        for m in history_msgs:
            if m.id and user_msg.id and m.id == user_msg.id:
                continue
            payload_messages.append(
                AIMessagePayload(
                    role="user" if m.sender == "USER" else "assistant",
                    content=m.content,
                )
            )

        # Ensure the current user prompt is guaranteed at the tail of messages
        payload_messages.append(
            AIMessagePayload(
                role="user",
                content=cleaned_prompt,
            )
        )

        user_roles = (
            UserRepository.get_user_role_names(current_user) if current_user else ["GUEST"]
        )
        is_staff = any(r in ["STAFF", "ADMIN"] for r in user_roles)
        effective_tools = (
            CUSTOMER_TOOL_DEFINITIONS + ADMIN_TOOL_DEFINITIONS
            if is_staff
            else CUSTOMER_TOOL_DEFINITIONS
        )

        system_prompt = AIGuardrails.build_system_prompt(
            user_name=current_user.full_name if current_user else None,
            role=user_roles[0],
        )

        # 7. Initial Query to AI Provider with automatic fallback
        try:
            provider_resp = await provider.generate_response(
                messages=payload_messages,
                tools=effective_tools,
                system_prompt=system_prompt,
            )
        except Exception as e:
            from app.integrations.ai.fallback import get_fallback_response
            fallback_text, intent = get_fallback_response(
                db=db,
                message=cleaned_prompt,
                current_user=current_user,
            )
            asst_msg = AIMessage(
                conversation_id=conversation.id,
                sender="ASSISTANT",
                content=fallback_text,
                tokens_used=max(1, (len(cleaned_prompt) + len(fallback_text)) // 4),
                created_at=datetime.now(timezone.utc),
            )
            db.add(asst_msg)
            db.commit()

            return AIChatResponse(
                session_uuid=conversation.session_uuid,
                message=fallback_text,
                suggested_prompts=["Kiểm tra đơn hàng", "Tìm sách hay", "Phí vận chuyển"],
                structured_payload={"is_fallback": True, "intent": intent, "error_details": str(e)},
                created_at=datetime.now(timezone.utc),
            )

        structured_payload: Dict[str, Any] = {}
        tool_results_list = []
        executed_tool_calls_data = []

        # 8. Handle Tool Calling Loop if requested
        if provider_resp.tool_calls:
            for tc in provider_resp.tool_calls:
                start_time = time.time()
                executed_tool_calls_data.append(tc.model_dump())

                # Execute backend domain tool within security context
                tool_output = AIToolExecutor.execute(
                    db=db,
                    tool_name=tc.name,
                    arguments=tc.arguments,
                    current_user=current_user,
                )
                duration_ms = int((time.time() - start_time) * 1000)

                # Collect structured payloads for frontend presentation
                if tool_output.get("confirmation_required"):
                    structured_payload["confirmation"] = {
                        "confirmation_token": tool_output.get("confirmation_token"),
                        "action_type": tool_output.get("action_type"),
                        "preview": tool_output.get("preview"),
                        "message": tool_output.get("message"),
                        "book_id": tool_output.get("book_id"),
                    }
                elif "total_revenue" in tool_output:
                    structured_payload["sales_summary"] = tool_output
                elif "low_stock_books" in tool_output:
                    structured_payload["low_stock"] = tool_output
                elif "total_physical_stock" in tool_output:
                    structured_payload["inventory_summary"] = tool_output
                elif "draft" in tool_output:
                    structured_payload["marketing_draft"] = tool_output
                elif "books" in tool_output:
                    structured_payload["books"] = tool_output["books"]
                elif "book" in tool_output:
                    structured_payload["book"] = tool_output["book"]
                elif "orders" in tool_output:
                    structured_payload["orders"] = tool_output["orders"]
                elif "order_code" in tool_output and "timeline" in tool_output:
                    structured_payload["tracking"] = tool_output
                elif "cart_total_items" in tool_output:
                    structured_payload["cart_update"] = tool_output
                elif "recommendations" in tool_output:
                    structured_payload["books"] = tool_output["recommendations"]

                tool_results_list.append({"tool": tc.name, "output": tool_output})

                # Determine execution status
                status_code = "SUCCESS"
                if not tool_output.get("success", False):
                    status_code = tool_output.get("error_code", "ERROR")
                elif tool_output.get("confirmation_required"):
                    status_code = "CONFIRMATION_REQUIRED"

                # Record mandatory persistent AI Action Audit Log
                existing_log = None
                if tool_output.get("confirmation_token"):
                    existing_log = (
                        db.query(AIActionLog)
                        .filter(AIActionLog.confirmation_token == tool_output["confirmation_token"])
                        .first()
                    )

                if existing_log:
                    existing_log.conversation_id = conversation.id
                    existing_log.execution_duration_ms = duration_ms
                    db.commit()
                else:
                    action_log = AIActionLog(
                        conversation_id=conversation.id,
                        user_id=current_user.id if current_user else None,
                        user_role=user_roles[0],
                        tool_name=tc.name,
                        input_arguments=AIGuardrails.mask_sensitive_data(tc.arguments),
                        execution_status=status_code,
                        confirmation_token=tool_output.get("confirmation_token"),
                        is_confirmed=False,
                        output_summary=str(tool_output)[:500],
                        execution_duration_ms=duration_ms,
                        created_at=datetime.now(timezone.utc),
                    )
                    db.add(action_log)
                    db.commit()

                # Append tool result turn for model synthesis
                payload_messages.append(
                    AIMessagePayload(
                        role="tool",
                        name=tc.name,
                        tool_call_id=tc.id,
                        content=json.dumps(tool_output, ensure_ascii=False),
                    )
                )

            # Query provider again with tool execution output
            provider_resp = await provider.generate_response(
                messages=payload_messages,
                tools=effective_tools,
                system_prompt=system_prompt,
            )

        final_text = (
            provider_resp.content
            or provider_resp.error_message
            or "Dạ, Novelia AI đã xử lý xong yêu cầu của Quý khách."
        )

        # 9. Store Assistant Response in DB
        assistant_msg = AIMessage(
            conversation_id=conversation.id,
            sender="ASSISTANT",
            content=final_text,
            tool_calls=executed_tool_calls_data if executed_tool_calls_data else None,
            tool_results=tool_results_list if tool_results_list else None,
            tokens_used=provider_resp.tokens_used,
            created_at=datetime.now(timezone.utc),
        )
        db.add(assistant_msg)
        conversation.updated_at = datetime.now(timezone.utc)
        db.commit()

        # 10. Generate Contextual Suggested Prompts
        if is_staff:
            suggested = [
                "📊 Báo cáo doanh thu và KPI",
                "📦 Tình trạng kho hàng toàn hệ thống",
                "⚠️ Sách sắp hết hàng cần nhập",
                "🛒 Tra cứu đơn hàng gần đây",
            ]
        else:
            suggested = [
                "📚 Gợi ý sách bán chạy nhất",
                "🔍 Sách kinh tế dưới 150k",
                "📦 Tra cứu đơn hàng của tôi",
                "🚚 Chính sách miễn phí vận chuyển",
            ]

        return AIChatResponse(
            session_uuid=conversation.session_uuid,
            message=final_text,
            suggested_prompts=suggested,
            structured_payload=structured_payload if structured_payload else None,
            created_at=datetime.now(timezone.utc),
        )

    @classmethod
    def confirm_action(
        cls,
        db: Session,
        confirmation_token: str,
        staff_user: User,
    ) -> AIConfirmResponse:
        """Execute confirmed mutating AI action after re-validating preconditions."""
        res = AIToolExecutor.execute_confirmation(
            db=db,
            confirmation_token=confirmation_token,
            staff_user=staff_user,
        )
        return AIConfirmResponse(
            success=res["success"],
            action_type=res["action_type"],
            message=res["message"],
            details=res.get("details"),
            executed_at=res["executed_at"],
        )

    @classmethod
    def list_user_conversations(
        cls, db: Session, user_id: int
    ) -> List[AIConversationRead]:
        """Fetch all conversation sessions belonging to the user."""
        convs = (
            db.query(AIConversation)
            .filter(AIConversation.user_id == user_id)
            .order_by(AIConversation.updated_at.desc())
            .all()
        )
        result = []
        for c in convs:
            result.append(
                AIConversationRead(
                    id=c.id,
                    session_uuid=c.session_uuid,
                    title=c.title,
                    conversation_type=c.conversation_type,
                    message_count=len(c.messages),
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                )
            )
        return result

    @classmethod
    def get_conversation_messages(
        cls,
        db: Session,
        session_uuid: str,
        current_user: Optional[User] = None,
    ) -> List[AIMessageRead]:
        """Retrieve full message history for a specific conversation session."""
        conv = (
            db.query(AIConversation)
            .filter(AIConversation.session_uuid == session_uuid)
            .first()
        )
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy phiên hội thoại '{session_uuid}'.",
            )

        # Anti-IDOR: If conversation belongs to another user, restrict access unless staff
        if conv.user_id:
            user_roles = (
                UserRepository.get_user_role_names(current_user) if current_user else []
            )
            is_staff = any(r in ["STAFF", "ADMIN"] for r in user_roles)
            if not is_staff and (not current_user or current_user.id != conv.user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bạn không có quyền truy cập lịch sử cuộc trò chuyện này.",
                )

        messages = (
            db.query(AIMessage)
            .filter(AIMessage.conversation_id == conv.id)
            .order_by(AIMessage.created_at.asc())
            .all()
        )
        return [AIMessageRead.model_validate(m) for m in messages]

    @classmethod
    def get_health_status(cls) -> AIHealthResponse:
        """Inspect current AI provider adapter and configuration realism."""
        provider = get_ai_provider()
        health = provider.check_health()
        return AIHealthResponse(
            status=health.status,
            provider=health.provider_name,
            model=health.model,
            is_configured=health.is_configured,
            details=health.details,
        )
