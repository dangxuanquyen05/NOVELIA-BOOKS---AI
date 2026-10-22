"""Google Gemini REST API Integration Provider with Function Calling."""

import json
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.integrations.ai.base import (
    AIMessagePayload,
    AIProvider,
    AIProviderHealth,
    AIProviderResponse,
    ToolCall,
    ToolDefinition,
)

logger = logging.getLogger(__name__)


class GeminiAIProvider(AIProvider):
    """Production adapter communicating with Google Gemini API."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY.strip()
        self.model = settings.GEMINI_MODEL.strip() or "gemini-1.5-flash"
        self.timeout = float(settings.AI_TIMEOUT_SECONDS)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def check_health(self) -> AIProviderHealth:
        """Verify API key availability and configuration."""
        if not self.api_key:
            return AIProviderHealth(
                status="MISSING_API_KEY",
                provider_name="gemini",
                model=self.model,
                is_configured=False,
                details="GEMINI_API_KEY chưa được cấu hình trong file .env hoặc biến môi trường backend.",
            )

        return AIProviderHealth(
            status="CONFIGURED",
            provider_name="gemini",
            model=self.model,
            is_configured=True,
            details=f"Đã cấu hình Gemini API với mô hình {self.model}.",
        )

    async def generate_response(
        self,
        messages: List[AIMessagePayload],
        tools: Optional[List[ToolDefinition]] = None,
        system_prompt: Optional[str] = None,
    ) -> AIProviderResponse:
        """Call Gemini generateContent endpoint with system prompt and function declarations."""
        if not self.api_key:
            return AIProviderResponse(
                is_error=True,
                error_message="Chưa cấu hình GEMINI_API_KEY trên máy chủ. Vui lòng cập nhật cấu hình backend.",
            )

        endpoint = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"

        # 1. Format contents for Gemini
        gemini_contents = []
        for msg in messages:
            role = "user" if msg.role in ["user", "tool"] else "model"
            parts = []

            if msg.role == "tool":
                # Function response part
                tool_result_content = {}
                try:
                    tool_result_content = json.loads(msg.content or "{}")
                except Exception:
                    tool_result_content = {"output": msg.content}

                parts.append({
                    "functionResponse": {
                        "name": msg.name or "tool_result",
                        "response": {"result": tool_result_content},
                    }
                })
            else:
                if msg.content:
                    parts.append({"text": msg.content})

                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        parts.append({
                            "functionCall": {
                                "name": tc.name,
                                "args": tc.arguments,
                            }
                        })

            if parts:
                gemini_contents.append({"role": role, "parts": parts})

        request_body: Dict[str, Any] = {
            "contents": gemini_contents,
            "generationConfig": {
                "temperature": 0.4,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            },
        }

        # 2. System instruction if provided
        if system_prompt:
            request_body["system_instruction"] = {
                "parts": [{"text": system_prompt}]
            }

        # 3. Add function declarations if tools provided
        if tools:
            func_decls = []
            for t in tools:
                func_decls.append({
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                })
            request_body["tools"] = [{"function_declarations": func_decls}]

        # 4. Execute HTTP Post
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(endpoint, json=request_body)

                if res.status_code != 200:
                    err_text = res.text
                    logger.error(f"Gemini API returned error {res.status_code}: {err_text}")
                    return AIProviderResponse(
                        is_error=True,
                        error_message=f"Gemini API lỗi ({res.status_code}): {err_text[:200]}",
                    )

                data = res.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return AIProviderResponse(content="Dạ, Novelia AI chưa nhận được câu trả lời từ mô hình. Vui lòng thử lại.")

                candidate = candidates[0]
                content_obj = candidate.get("content", {})
                parts = content_obj.get("parts", [])

                text_response = ""
                tool_calls_emitted: List[ToolCall] = []

                for idx, part in enumerate(parts):
                    if "text" in part:
                        text_response += part["text"]
                    if "functionCall" in part:
                        fc = part["functionCall"]
                        tool_calls_emitted.append(
                            ToolCall(
                                id=f"call_{idx}_{fc.get('name')}",
                                name=fc.get("name"),
                                arguments=fc.get("args", {}),
                            )
                        )

                tokens = data.get("usageMetadata", {}).get("totalTokenCount")

                return AIProviderResponse(
                    content=text_response.strip() if text_response else None,
                    tool_calls=tool_calls_emitted if tool_calls_emitted else None,
                    tokens_used=tokens,
                )

        except httpx.TimeoutException:
            logger.warning("Gemini API call timed out after configured threshold.")
            return AIProviderResponse(
                is_error=True,
                error_message="Kết nối tới mô hình AI đã hết thời gian chờ (Timeout). Vui lòng thử lại sau.",
            )
        except Exception as exc:
            logger.error(f"Unhandled Gemini API failure: {str(exc)}")
            return AIProviderResponse(
                is_error=True,
                error_message=f"Lỗi kết nối tới AI Provider: {str(exc)}",
            )
