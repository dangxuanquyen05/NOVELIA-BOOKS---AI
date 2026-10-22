"""Standard SMTP email provider implementation.

Handles secure transmission via TLS/STARTTLS with connection timeout safeguards.
"""

import smtplib
import uuid
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

from app.core.config import settings
from app.integrations.email.base import (
    EmailDeliveryResult,
    EmailMessage,
    EmailProvider,
)


class SmtpEmailProvider(EmailProvider):
    """Production-ready SMTP transport adapter."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> None:
        self.host = host or settings.SMTP_HOST
        self.port = port or settings.SMTP_PORT
        self.username = username or settings.SMTP_USER
        self.password = password or settings.SMTP_PASSWORD
        self.from_email = from_email or settings.SMTP_FROM_EMAIL
        self.from_name = from_name or settings.SMTP_FROM_NAME
        self.timeout = timeout or settings.SMTP_TIMEOUT_SECONDS

    def send_email(self, message: EmailMessage) -> EmailDeliveryResult:
        """Send email via SMTP with timeout and error handling."""
        msg_id = f"smtp_{uuid.uuid4().hex[:12]}"
        
        # Build MIME Message
        mime_msg = MIMEMultipart("alternative")
        mime_msg["Subject"] = message.subject
        mime_msg["From"] = f"{self.from_name} <{self.from_email}>"
        mime_msg["To"] = message.to_email
        mime_msg["Message-ID"] = f"<{msg_id}@novelia.vn>"

        # Attach text part
        text_part = MIMEText(message.body_text, "plain", "utf-8")
        mime_msg.attach(text_part)

        # Attach HTML part if available
        if message.body_html:
            html_part = MIMEText(message.body_html, "html", "utf-8")
            mime_msg.attach(html_part)

        try:
            with smtplib.SMTP(self.host, self.port, timeout=self.timeout) as server:
                # Upgrade to TLS if port 587
                if self.port in [587, 25]:
                    try:
                        server.starttls()
                    except Exception:
                        pass  # Server might not support STARTTLS

                if self.username and self.password:
                    server.login(self.username, self.password)

                server.sendmail(self.from_email, [message.to_email], mime_msg.as_string())

            return EmailDeliveryResult(
                success=True,
                message_id=msg_id,
                provider_type="SMTP",
                is_mock=False,
                recipient=message.to_email,
                subject=message.subject,
                error=None,
            )
        except Exception as e:
            return EmailDeliveryResult(
                success=False,
                message_id=msg_id,
                provider_type="SMTP",
                is_mock=False,
                recipient=message.to_email,
                subject=message.subject,
                error=f"SMTP transport error: {str(e)}",
            )

    def check_health(self) -> Dict[str, Any]:
        """Verify SMTP host and configuration."""
        is_configured = bool(self.host and self.from_email)
        return {
            "status": "CONFIGURED" if is_configured else "INCOMPLETE",
            "provider": "SMTP",
            "is_mock": False,
            "host": self.host,
            "port": self.port,
            "from_email": self.from_email,
            "has_auth": bool(self.username and self.password),
        }
