"""Factory for instantiating decoupled AI Provider adapters."""

from typing import Optional
from app.core.config import settings
from app.integrations.ai.base import AIProvider
from app.integrations.ai.gemini import GeminiAIProvider
from app.integrations.ai.mock import MockAIProvider


def get_ai_provider(provider_type: Optional[str] = None) -> AIProvider:
    """Resolve and instantiate configured AI Provider."""
    selected = (provider_type or settings.AI_PROVIDER).strip().lower()

    if selected == "gemini":
        return GeminiAIProvider()
    elif selected == "mock":
        return MockAIProvider()

    # Fallback default
    return MockAIProvider()
