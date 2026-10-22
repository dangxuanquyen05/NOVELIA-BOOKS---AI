"""Abstract Base Classes and Data Contracts for AI Provider Integrations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    """Pydantic definition for schema-validated tools presented to LLMs."""

    name: str = Field(..., description="Unique tool identifier")
    description: str = Field(..., description="Clear explanation of tool function")
    parameters: Dict[str, Any] = Field(..., description="JSON Schema for parameters")


class ToolCall(BaseModel):
    """Normalized representation of a tool call emitted by an LLM."""

    id: str = Field(..., description="Unique ID for this tool call execution")
    name: str = Field(..., description="Target tool name to invoke")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Parsed arguments dict")


class AIMessagePayload(BaseModel):
    """Normalized conversational turn across provider formats."""

    role: str = Field(..., description="One of: 'system', 'user', 'assistant', 'tool'")
    content: Optional[str] = Field(None, description="Message text content")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="Tools invoked by model")
    tool_call_id: Optional[str] = Field(None, description="Corresponding tool call ID if role is tool")
    name: Optional[str] = Field(None, description="Tool name if role is tool")


class AIProviderResponse(BaseModel):
    """Standardized output from any underlying LLM provider."""

    content: Optional[str] = Field(None, description="Generated assistant text response")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="List of tool calls to execute")
    tokens_used: Optional[int] = Field(None, description="Approximate or exact tokens utilized")
    is_error: bool = Field(False, description="Whether execution encountered an unhandled error")
    error_message: Optional[str] = Field(None, description="Sanitized error description")


class AIProviderHealth(BaseModel):
    """Diagnostic health state for the AI provider."""

    status: str = Field(..., description="'CONFIGURED', 'MISSING_API_KEY', 'UNAVAILABLE', 'MOCK_READY'")
    provider_name: str = Field(..., description="Provider identity (e.g., 'gemini', 'mock')")
    model: str = Field(..., description="Configured model name")
    is_configured: bool = Field(..., description="True if credentials and dependencies are met")
    details: str = Field(..., description="Human-readable status summary")


class AIProvider(ABC):
    """Abstract interface defining required methods for LLM integrations."""

    @abstractmethod
    async def generate_response(
        self,
        messages: List[AIMessagePayload],
        tools: Optional[List[ToolDefinition]] = None,
        system_prompt: Optional[str] = None,
    ) -> AIProviderResponse:
        """Query LLM provider with conversational context and available tools."""
        pass

    @abstractmethod
    def check_health(self) -> AIProviderHealth:
        """Inspect provider configuration and return health report."""
        pass
