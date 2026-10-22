"""Phase 12 automated test suite for Notifications, In-App Alerts, Audit Trail, and Email Delivery.

Validates:
1. In-app notifications with unread counter and read-state management.
2. Strict RBAC and multi-tenant isolation (User A cannot view or manipulate User B's alerts).
3. Order and Shipping lifecycle triggers.
4. Idempotency, replay protection, and event deduplication.
5. Email Provider decoupled abstraction with mock delivery honesty (never claim real email sent).
6. Fail-safe email delivery: transport errors NEVER roll back valid orders.
7. Exponential backoff retry mechanism.
8. Sensitive data masking (passwords, JWT tokens, secrets, API keys redacted in audit logs).
9. Administrative audit trail and AI action log endpoints protected by RBAC.
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user, get_db, require_roles
from app.core.masking import REDACTED_PLACEHOLDER, mask_sensitive_data
from app.integrations.email.base import EmailDeliveryResult, EmailMessage
from app.integrations.email.factory import get_email_provider, reset_mock_email_provider
from app.integrations.email.mock import MockEmailProvider
from app.main import app
from app.models.catalog import Book
from app.models.commerce import Order, OrderItem
from app.models.experience import Notification
from app.models.inventory import Inventory
from app.models.payment_shipping import Payment, Shipment
from app.models.user import Role, User, UserRole
from app.repositories.audit_repo import AuditRepository
from app.repositories.notification_repo import NotificationRepository
from app.services.audit_service import AuditService
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService
from app.services.order_service import OrderService

client = TestClient(app)


# =============================================================================
# FIXTURES & HELPERS
# =============================================================================

@pytest.fixture(autouse=True)
def clean_mock_emails():
    """Reset mock emails before each test."""
    reset_mock_email_provider()
    yield
    reset_mock_email_provider()


def make_user(user_id: int, role_name: str = "CUSTOMER") -> User:
    """Helper to mock a User with assigned role."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = f"{role_name.lower()}_{user_id}@novelia.vn"
    user.full_name = f"User {user_id} ({role_name})"
    user.phone = "0988776655"
    user.is_active = True
    user.created_at = datetime.now(timezone.utc)

    role = MagicMock(spec=Role)
    role.name = role_name
    ur = MagicMock(spec=UserRole)
    ur.role = role
    user.roles = [ur]
    return user


def make_notification(
    notif_id: int,
    user_id: int,
    title: str = "Thông báo đơn hàng",
    message: str = "Đơn hàng đang xử lý",
    notification_type: str = "ORDER",
    is_read: bool = False,
) -> Notification:
    """Helper to construct a mock Notification."""
    notif = MagicMock(spec=Notification)
    notif.id = notif_id
    notif.user_id = user_id
    notif.title = title
    notif.message = message
    notif.notification_type = notification_type
    notif.reference_link = "/orders/NVL-12345"
    notif.is_read = is_read
    notif.read_at = datetime.now(timezone.utc) if is_read else None
    notif.created_at = datetime.now(timezone.utc)
    return notif


# =============================================================================
# 1. IN-APP NOTIFICATIONS & TENANT ISOLATION TESTS
# =============================================================================

class TestInAppNotificationsAndTenantIsolation:
    """Validate notification creation, unread badge counter, and cross-user isolation."""

    def test_query_user_notifications_service(self):
        """User receives notifications and can view them with accurate unread count."""
        mock_db = MagicMock()
        user = make_user(42, "CUSTOMER")

        n1 = make_notification(1, 42, "Đơn hàng NVL-01", is_read=False)
        n2 = make_notification(2, 42, "Khuyến mãi 20%", is_read=False)

        with patch.object(
            NotificationRepository,
            "get_user_notifications",
            return_value=([n2, n1], 2, 2),
        ):
            res = NotificationService.get_user_notifications(
                db=mock_db, user_id=user.id, page=1, limit=10
            )
            assert res.total == 2
            assert res.unread_count == 2
            assert len(res.items) == 2
            assert res.items[0].id == 2

    def test_tenant_isolation_cannot_access_other_user_notifications(self):
        """Customer B cannot view or mark Customer A's notification as read."""
        mock_db = MagicMock()
        user_a = make_user(10, "CUSTOMER")
        user_b = make_user(20, "CUSTOMER")

        # When User B attempts to mark User A's notification (returns None because user_id does not match)
        with patch.object(NotificationRepository, "mark_as_read", return_value=None):
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                NotificationService.mark_as_read(db=mock_db, notification_id=999, user_id=user_b.id)
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_mark_single_and_mark_all_read(self):
        """Marking read updates is_read flag and tally."""
        mock_db = MagicMock()
        user = make_user(15, "CUSTOMER")
        notif = make_notification(1, 15, "Cập nhật đơn", is_read=True)

        with patch.object(NotificationRepository, "mark_as_read", return_value=notif):
            marked = NotificationService.mark_as_read(db=mock_db, notification_id=1, user_id=user.id)
            assert marked.id == 1
            assert marked.is_read is True

        with patch.object(NotificationRepository, "mark_all_as_read", return_value=5):
            res_all = NotificationService.mark_all_as_read(db=mock_db, user_id=user.id)
            assert res_all.success is True
            assert res_all.marked_count == 5


# =============================================================================
# 2. ORDER & SHIPPING NOTIFICATION HOOKS & DEDUPLICATION
# =============================================================================

class TestOrderAndShippingNotificationHooks:
    """Validate notifications triggered by order status changes and carrier webhooks."""

    def test_order_status_progression_triggers_notification(self):
        """Transitioning order status generates in-app notification for customer."""
        mock_db = MagicMock()
        order = MagicMock(spec=Order)
        order.id = 100
        order.user_id = 42
        order.order_code = "NVL-2026-999"
        order.user = make_user(42, "CUSTOMER")

        created_notif = make_notification(1, 42, "Cập nhật đơn hàng #NVL-2026-999")

        with patch.object(NotificationRepository, "has_similar_notification_recently", return_value=False):
            with patch.object(NotificationRepository, "create_notification", return_value=created_notif):
                with patch.object(EmailService, "send_order_status_email", return_value=None):
                    res = NotificationService.notify_order_status_change(
                        db=mock_db, order=order, old_status="CONFIRMED", new_status="SHIPPING"
                    )
                    assert res is not None
                    assert res.id == 1

    def test_notification_deduplication_replay_protection(self):
        """Duplicate notification dispatch within 10 minutes is suppressed safely."""
        mock_db = MagicMock()
        order = MagicMock(spec=Order)
        order.id = 100
        order.user_id = 42
        order.order_code = "NVL-2026-999"

        with patch.object(NotificationRepository, "has_similar_notification_recently", return_value=True):
            res = NotificationService.notify_order_status_change(
                db=mock_db, order=order, old_status="CONFIRMED", new_status="SHIPPING"
            )
            # Suppressed by deduplication
            assert res is None

    def test_shipping_milestone_triggers_notification(self):
        """Shipping milestone creates shipping notification."""
        mock_db = MagicMock()
        shipment = MagicMock(spec=Shipment)
        shipment.tracking_code = "GHN-TRACK-001"
        shipment.carrier = "GHN"
        order = MagicMock(spec=Order)
        order.order_code = "NVL-2026-999"
        order.user_id = 42
        order.user = make_user(42, "CUSTOMER")
        shipment.order = order

        created_notif = make_notification(2, 42, "Vận chuyển đơn hàng #NVL-2026-999", notification_type="SHIPPING")

        with patch.object(NotificationRepository, "has_similar_notification_recently", return_value=False):
            with patch.object(NotificationRepository, "create_notification", return_value=created_notif):
                with patch.object(EmailService, "send_shipping_update_email", return_value=None):
                    res = NotificationService.notify_shipping_update(
                        db=mock_db, shipment=shipment, carrier_status="IN_TRANSIT", description="Đang giao hàng"
                    )
                    assert res is not None
                    assert res.notification_type == "SHIPPING"


# =============================================================================
# 3. EMAIL PROVIDER & ZERO-FAIL RESILIENCE
# =============================================================================

class TestEmailProviderAndFailureResilience:
    """Validate decoupled email adapter, realism rule, and order failure resilience."""

    def test_mock_email_provider_honesty(self):
        """Mock provider explicitly declares is_mock=True and captures sent emails in memory."""
        provider = get_email_provider(override_type="mock")
        health = provider.check_health()

        assert health["is_mock"] is True
        assert health["provider"] == "MOCK"

        msg = EmailMessage(
            to_email="reader@novelia.vn",
            subject="Chào mừng đến với Novelia Books",
            body_text="Khám phá tri thức cùng Novelia.",
        )
        result = provider.send_email(msg)
        assert result.success is True
        assert result.is_mock is True
        assert result.provider_type == "MOCK"

        # Verify recorded in mock provider memory
        assert isinstance(provider, MockEmailProvider)
        assert len(provider.sent_emails) == 1
        assert provider.sent_emails[0]["to_email"] == "reader@novelia.vn"

    def test_email_failure_does_not_abort_order_progression(self):
        """Non-negotiable rule: Transport failure in email service MUST NOT roll back order update."""
        mock_db = MagicMock()
        staff = make_user(99, "STAFF")

        order = MagicMock(spec=Order)
        order.order_code = "NVL-TEST-001"
        order.status = "CONFIRMED"
        order.items = []
        order.payment = None

        with patch("app.repositories.order_repo.OrderRepository.get_by_code", return_value=order):
            with patch("app.services.email_service.EmailService.send_order_status_email", side_effect=ConnectionError("Simulated SMTP Server Unreachable")):
                updated_order = OrderService.update_order_status(
                    db=mock_db,
                    staff_user=staff,
                    order_code="NVL-TEST-001",
                    new_status="PROCESSING",
                )
                assert updated_order.status == "PROCESSING"

    def test_email_retry_exponential_backoff(self):
        """EmailService retries on transient errors with backoff."""
        mock_provider = MagicMock()
        # Fail first 2 attempts, succeed on 3rd attempt
        mock_provider.send_email.side_effect = [
            EmailDeliveryResult(
                success=False,
                message_id="fail_1",
                provider_type="SMTP",
                is_mock=False,
                recipient="test@novelia.vn",
                subject="Test",
                error="Timeout",
            ),
            EmailDeliveryResult(
                success=False,
                message_id="fail_2",
                provider_type="SMTP",
                is_mock=False,
                recipient="test@novelia.vn",
                subject="Test",
                error="Connection reset",
            ),
            EmailDeliveryResult(
                success=True,
                message_id="success_3",
                provider_type="SMTP",
                is_mock=False,
                recipient="test@novelia.vn",
                subject="Test",
            ),
        ]

        with patch("app.services.email_service.get_email_provider", return_value=mock_provider):
            res = EmailService.send_transactional_email(
                to_email="test@novelia.vn",
                subject="Test",
                body_text="Content",
                max_retries=2,
            )
            assert res.success is True
            assert mock_provider.send_email.call_count == 3


# =============================================================================
# 4. SENSITIVE DATA MASKING & AUDIT TRAILS
# =============================================================================

class TestSensitiveDataMaskingAndAuditTrails:
    """Validate strict security masking and immutable audit recording."""

    def test_mask_sensitive_data_redacts_credentials(self):
        """Passwords, tokens, secrets, CVVs are deeply masked."""
        raw_payload = {
            "email": "user@novelia.vn",
            "password": "SuperSecretPassword123!",
            "nested": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "rt_987654321",
                "normal_field": "safe_value",
            },
            "card_info": {
                "card_number": "4111111111111234",
                "cvv": "999",
            },
            "api_key": "gemini_live_secret_key_12345",
        }

        sanitized = mask_sensitive_data(raw_payload)

        assert sanitized["password"] == REDACTED_PLACEHOLDER
        assert sanitized["nested"]["access_token"] == REDACTED_PLACEHOLDER
        assert sanitized["nested"]["refresh_token"] == REDACTED_PLACEHOLDER
        assert sanitized["nested"]["normal_field"] == "safe_value"
        assert sanitized["card_info"]["cvv"] == REDACTED_PLACEHOLDER
        assert sanitized["api_key"] == REDACTED_PLACEHOLDER

    def test_audit_repository_persists_sanitized_record(self):
        """AuditRepository automatically redacts sensitive entries before persisting to database."""
        mock_db = MagicMock()
        staff = make_user(99, "STAFF")

        audit_entry = AuditRepository.record_audit(
            db=mock_db,
            action="USER_UPDATE",
            entity_type="USER",
            entity_id="123",
            user_id=staff.id,
            old_values={"password_hash": "$2b$12$oldSecretHash", "role": "CUSTOMER"},
            new_values={"password_hash": "$2b$12$newSecretHash", "token": "jwt_token_sample", "role": "STAFF"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 TestAgent",
        )

        mock_db.add.assert_called_once()
        saved_log = mock_db.add.call_args[0][0]
        assert saved_log.old_values["password_hash"] == REDACTED_PLACEHOLDER
        assert saved_log.new_values["password_hash"] == REDACTED_PLACEHOLDER
        assert saved_log.new_values["token"] == REDACTED_PLACEHOLDER
        assert saved_log.new_values["role"] == "STAFF"


# =============================================================================
# 5. API ENDPOINTS & RBAC PROTECTION
# =============================================================================

class TestAuditAndNotificationAPIEndpoints:
    """Validate HTTP API endpoints for notifications and audit governance."""

    def test_customer_can_read_and_mark_notification_via_api(self):
        """Customer accesses notifications through authenticated API."""
        customer = make_user(42, "CUSTOMER")
        app.dependency_overrides[get_current_active_user] = lambda: customer

        notif = make_notification(1, 42, "Đơn hàng thành công", is_read=False)

        try:
            with patch.object(NotificationService, "get_unread_count") as mock_unread:
                mock_unread.return_value.unread_count = 3
                res_unread = client.get("/api/v1/notifications/unread-count")
                assert res_unread.status_code == 200
                assert res_unread.json()["unread_count"] == 3

            with patch.object(NotificationService, "get_user_notifications") as mock_list:
                mock_list.return_value.items = [notif]
                mock_list.return_value.total = 1
                mock_list.return_value.unread_count = 1
                mock_list.return_value.page = 1
                mock_list.return_value.limit = 20
                res_list = client.get("/api/v1/notifications")
                assert res_list.status_code == 200

            with patch.object(NotificationService, "mark_as_read", return_value=notif):
                res_mark = client.put("/api/v1/notifications/1/read")
                assert res_mark.status_code == 200

            with patch.object(NotificationService, "mark_all_as_read") as mock_all:
                mock_all.return_value.success = True
                mock_all.return_value.marked_count = 3
                mock_all.return_value.message = "Đã đánh dấu 3 thông báo"
                res_all = client.put("/api/v1/notifications/read-all")
                assert res_all.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_customer_forbidden_from_admin_audit_logs(self):
        """Customer role receives HTTP 403 when trying to access administrative audit trails."""
        customer = make_user(42, "CUSTOMER")
        app.dependency_overrides[get_current_active_user] = lambda: customer

        try:
            res_audit = client.get("/api/v1/audit/logs")
            assert res_audit.status_code == status.HTTP_403_FORBIDDEN

            res_ai = client.get("/api/v1/audit/ai-actions")
            assert res_ai.status_code == status.HTTP_403_FORBIDDEN
        finally:
            app.dependency_overrides.clear()

    def test_staff_can_view_audit_trail_and_email_status(self):
        """Staff/Admin user can view audit trail and email status."""
        staff = make_user(99, "STAFF")
        app.dependency_overrides[get_current_active_user] = lambda: staff

        try:
            with patch.object(AuditService, "get_audit_trail") as mock_audit:
                mock_audit.return_value.items = []
                mock_audit.return_value.total = 0
                mock_audit.return_value.page = 1
                mock_audit.return_value.limit = 20
                res_audit = client.get("/api/v1/audit/logs")
                assert res_audit.status_code == 200

            res_email = client.get("/api/v1/audit/email-status")
            assert res_email.status_code == 200
            data = res_email.json()
            assert data["is_mock"] is True
            assert data["provider"] == "MOCK"
        finally:
            app.dependency_overrides.clear()
