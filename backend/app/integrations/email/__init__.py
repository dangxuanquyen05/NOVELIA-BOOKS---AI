"""Email transport abstraction package."""

from app.integrations.email.base import (
    EmailDeliveryResult,
    EmailMessage,
    EmailProvider,
)
from app.integrations.email.factory import (
    get_email_provider,
    reset_mock_email_provider,
)
from app.integrations.email.mock import MockEmailProvider
from app.integrations.email.smtp import SmtpEmailProvider

__all__ = [
    "EmailMessage",
    "EmailDeliveryResult",
    "EmailProvider",
    "MockEmailProvider",
    "SmtpEmailProvider",
    "get_email_provider",
    "reset_mock_email_provider",
]
