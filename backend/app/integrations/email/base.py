"""Abstract base class and contract schemas for Email delivery providers.

Enforces provider decoupling between Mock, SMTP, and external transactional email gateways
(SendGrid, Mailgun, AWS SES) with strict realism regarding mock vs live delivery.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EmailMessage(BaseModel):
    """Normalized email payload for notifications and transactional updates."""

    to_email: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Subject line")
    body_text: str = Field(..., description="Plain-text body fallback")
    body_html: Optional[str] = Field(None, description="HTML formatted email body")
    template_name: Optional[str] = Field(None, description="Optional email template key")
    template_data: Optional[Dict[str, Any]] = Field(None, description="Variables for templating")
    reference_id: Optional[str] = Field(None, description="Order code or shipment tracking code")


class EmailDeliveryResult(BaseModel):
    """Standardized response from an email delivery attempt."""

    success: bool
    message_id: str
    provider_type: str  # 'MOCK', 'SMTP', 'SENDGRID', etc.
    is_mock: bool
    recipient: str
    subject: str
    error: Optional[str] = None
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmailProvider(ABC):
    """Decoupled interface for email transport."""

    @abstractmethod
    def send_email(self, message: EmailMessage) -> EmailDeliveryResult:
        """Send an email message synchronously or return delivery outcome."""
        pass

    @abstractmethod
    def check_health(self) -> Dict[str, Any]:
        """Verify transport connectivity, credentials, and configuration status."""
        pass
