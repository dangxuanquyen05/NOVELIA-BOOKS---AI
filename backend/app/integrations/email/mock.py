"""Mock email provider for development, integration tests, and sandbox verification.

Records all outbound emails in-memory for assertion and auditing without contacting
external mail servers or fabricating false claims of live internet delivery.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.integrations.email.base import (
    EmailDeliveryResult,
    EmailMessage,
    EmailProvider,
)


class MockEmailProvider(EmailProvider):
    """Safe mock adapter recording email dispatches in-memory."""

    def __init__(self) -> None:
        self.sent_emails: List[Dict[str, Any]] = []

    def send_email(self, message: EmailMessage) -> EmailDeliveryResult:
        """Simulate email sending and store the record for inspection."""
        msg_id = f"mock_mail_{uuid.uuid4().hex[:12]}"
        record = {
            "message_id": msg_id,
            "to_email": message.to_email,
            "subject": message.subject,
            "body_text": message.body_text,
            "body_html": message.body_html,
            "template_name": message.template_name,
            "template_data": message.template_data,
            "reference_id": message.reference_id,
            "sent_at": datetime.now(timezone.utc),
        }
        self.sent_emails.append(record)

        return EmailDeliveryResult(
            success=True,
            message_id=msg_id,
            provider_type="MOCK",
            is_mock=True,
            recipient=message.to_email,
            subject=message.subject,
            error=None,
        )

    def check_health(self) -> Dict[str, Any]:
        """Health status check."""
        return {
            "status": "HEALTHY",
            "provider": "MOCK",
            "is_mock": True,
            "total_sent_in_memory": len(self.sent_emails),
            "message": "Mock email provider is active. Outbound emails are captured in memory.",
        }

    def clear(self) -> None:
        """Reset in-memory sent mail log."""
        self.sent_emails.clear()
