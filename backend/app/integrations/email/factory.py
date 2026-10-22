"""Factory to resolve email provider based on environment and configuration."""

from typing import Optional

from app.core.config import settings
from app.integrations.email.base import EmailProvider
from app.integrations.email.mock import MockEmailProvider
from app.integrations.email.smtp import SmtpEmailProvider

_mock_instance: Optional[MockEmailProvider] = None


def get_email_provider(override_type: Optional[str] = None) -> EmailProvider:
    """Return the configured email provider singleton or instance."""
    global _mock_instance
    provider_name = (override_type or settings.EMAIL_PROVIDER).strip().lower()

    if provider_name == "smtp":
        return SmtpEmailProvider()

    # Default to singleton MockEmailProvider so sent emails can be inspected
    if _mock_instance is None:
        _mock_instance = MockEmailProvider()
    return _mock_instance


def reset_mock_email_provider() -> None:
    """Helper for testing to reset captured mock emails."""
    global _mock_instance
    if _mock_instance:
        _mock_instance.clear()
