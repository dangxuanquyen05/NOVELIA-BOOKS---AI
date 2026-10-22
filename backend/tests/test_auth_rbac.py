"""Tests for Phase 3 Authentication, RBAC, and Token Lifecycle.

Validates:
- Password hashing and bcrypt verification
- Token issuance, signature validation, expiration, and revocation
- RBAC role enforcement (CUSTOMER, STAFF, ADMIN)
- Duplicate email prevention (HTTP 409)
- Authentication failures (HTTP 401)
- Role escalation prevention (Registration forced to CUSTOMER)
- Tenant isolation on address management (HTTP 404 on cross-user access)
"""

from datetime import timedelta
from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.api.deps import require_roles
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    is_token_revoked,
    revoke_token,
    verify_password,
)
from app.database.connection import get_db
from app.main import app
from app.models.user import Role, User, UserAddress, UserRole
from app.schemas.auth import (
    ChangePasswordRequest,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.schemas.user import AddressCreateRequest, AddressUpdateRequest
from app.services.auth_service import AuthService
from app.services.user_service import UserService

client = TestClient(app)


class TestSecurityAndTokens:
    """Unit tests for password hashing and JWT token mechanics."""

    def test_bcrypt_hashing_and_verification(self):
        """Verify secure bcrypt hashing and matching."""
        raw_password = "SecurePassword2026!"
        hashed = get_password_hash(raw_password)

        assert hashed != raw_password
        assert hashed.startswith("$2b$")
        assert verify_password(raw_password, hashed) is True
        assert verify_password("IncorrectPassword", hashed) is False

    def test_jwt_access_token_creation_and_claims(self):
        """Verify JWT token embeds user identity and role claims."""
        token = create_access_token(
            user_id=42,
            email="reader@novelia.vn",
            roles=["CUSTOMER"],
            expires_delta=timedelta(minutes=15),
        )
        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == "42"
        assert payload["email"] == "reader@novelia.vn"
        assert payload["type"] == "access"
        assert "CUSTOMER" in payload["roles"]

    def test_jwt_expired_token(self):
        """Verify expired tokens are rejected."""
        # Create token that expired 5 minutes ago
        expired_token = create_access_token(
            user_id=42,
            email="expired@novelia.vn",
            roles=["CUSTOMER"],
            expires_delta=timedelta(minutes=-5),
        )
        payload = decode_token(expired_token)
        assert payload is None

    def test_token_revocation_logout(self):
        """Verify token revocation mechanism for immediate logout."""
        token = create_access_token(
            user_id=99,
            email="logout@novelia.vn",
            roles=["CUSTOMER"],
        )
        assert is_token_revoked(token) is False

        revoke_token(token)
        assert is_token_revoked(token) is True


class TestRBACAuthorization:
    """Unit tests for Role-Based Access Control logic."""

    def test_rbac_customer_allowed_customer_zone(self):
        """Verify CUSTOMER role can access customer-permitted endpoints."""
        mock_user = MagicMock(spec=User)
        customer_role = MagicMock()
        customer_role.name = "CUSTOMER"
        mock_user.roles = [MagicMock(role=customer_role)]

        checker = require_roles("CUSTOMER")
        result = checker(mock_user)
        assert result == mock_user

    def test_rbac_customer_denied_staff_zone(self):
        """Verify CUSTOMER role is blocked from STAFF zone with HTTP 403."""
        mock_user = MagicMock(spec=User)
        customer_role = MagicMock()
        customer_role.name = "CUSTOMER"
        mock_user.roles = [MagicMock(role=customer_role)]

        checker = require_roles("STAFF")
        with pytest.raises(HTTPException) as exc_info:
            checker(mock_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Insufficient" in exc_info.value.detail or "permitted" in exc_info.value.detail

    def test_rbac_admin_super_access(self):
        """Verify ADMIN role automatically passes all permission checks."""
        mock_user = MagicMock(spec=User)
        admin_role = MagicMock()
        admin_role.name = "ADMIN"
        mock_user.roles = [MagicMock(role=admin_role)]

        staff_checker = require_roles("STAFF")
        assert staff_checker(mock_user) == mock_user

        customer_checker = require_roles("CUSTOMER")
        assert customer_checker(mock_user) == mock_user


class TestAuthServiceBusinessLogic:
    """Unit tests for AuthService registration and authentication business rules."""

    def test_register_duplicate_email_raises_conflict(self):
        """Verify duplicate registration raises HTTP 409 Conflict."""
        mock_db = MagicMock()
        mock_existing = MagicMock(spec=User)

        with patch("app.repositories.user_repo.UserRepository.get_by_email", return_value=mock_existing):
            req = UserRegisterRequest(
                email="duplicate@novelia.vn",
                password="Password123!",
                full_name="Duplicate User",
            )
            with pytest.raises(HTTPException) as exc:
                AuthService.register_customer(mock_db, req)
            assert exc.value.status_code == status.HTTP_409_CONFLICT
            assert "already registered" in exc.value.detail

    def test_register_assigns_customer_role(self):
        """Verify registration always assigns CUSTOMER role and never ADMIN."""
        mock_db = MagicMock()
        mock_user = MagicMock(spec=User, id=10, email="new@novelia.vn")

        with patch("app.repositories.user_repo.UserRepository.get_by_email", return_value=None):
            with patch("app.repositories.user_repo.UserRepository.create_user", return_value=mock_user):
                with patch("app.repositories.user_repo.UserRepository.assign_role") as mock_assign:
                    req = UserRegisterRequest(
                        email="new@novelia.vn",
                        password="Password123!",
                        full_name="New Reader",
                    )
                    created = AuthService.register_customer(mock_db, req)
                    assert created == mock_user
                    mock_assign.assert_called_once_with(mock_db, user_id=10, role_name="CUSTOMER")

    def test_authenticate_invalid_password(self):
        """Verify wrong password raises HTTP 401 Unauthorized."""
        mock_db = MagicMock()
        hashed = get_password_hash("CorrectPassword123!")
        mock_user = MagicMock(spec=User, is_active=True, hashed_password=hashed)

        with patch("app.repositories.user_repo.UserRepository.get_by_email", return_value=mock_user):
            creds = UserLoginRequest(email="user@novelia.vn", password="WrongPassword!")
            with pytest.raises(HTTPException) as exc:
                AuthService.authenticate(mock_db, creds)
            assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid email or password" in exc.value.detail

    def test_change_password_mismatch_old(self):
        """Verify changing password fails when current password does not match."""
        mock_db = MagicMock()
        hashed = get_password_hash("ExistingPassword123!")
        mock_user = MagicMock(spec=User, id=1, hashed_password=hashed)

        req = ChangePasswordRequest(
            current_password="IncorrectCurrentPassword",
            new_password="NewPassword123!",
        )
        with pytest.raises(HTTPException) as exc:
            AuthService.change_password(mock_db, mock_user, req)
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Current password does not match" in exc.value.detail


class TestAddressTenantIsolation:
    """Unit tests ensuring customers can never view, mutate, or delete another user's addresses."""

    def test_update_address_other_user_denied(self):
        """Verify updating an address owned by another user returns HTTP 404."""
        mock_db = MagicMock()
        # Querying with user_id=10 for an address belonging to user_id=99 returns None
        with patch("app.repositories.user_repo.UserRepository.get_address_by_id", return_value=None):
            req = AddressUpdateRequest(recipient_name="Tampered Name")
            with pytest.raises(HTTPException) as exc:
                UserService.update_address(mock_db, user_id=10, address_id=999, data=req)
            assert exc.value.status_code == status.HTTP_404_NOT_FOUND
            assert "not found or access denied" in exc.value.detail

    def test_delete_address_other_user_denied(self):
        """Verify deleting an address owned by another user returns HTTP 404."""
        mock_db = MagicMock()
        with patch("app.repositories.user_repo.UserRepository.get_address_by_id", return_value=None):
            with pytest.raises(HTTPException) as exc:
                UserService.delete_address(mock_db, user_id=10, address_id=999)
            assert exc.value.status_code == status.HTTP_404_NOT_FOUND
            assert "not found or access denied" in exc.value.detail


class TestAPIEndpointsMocked:
    """Integration test suite for FastAPI endpoint handlers and responses."""

    def test_api_register_endpoint(self):
        """Verify POST /api/v1/auth/register handler."""
        mock_user = MagicMock(
            id=1,
            email="api_test@novelia.vn",
            full_name="API Reader",
            phone="0901234567",
            is_active=True,
            created_at="2026-10-20T00:00:00Z",
            updated_at="2026-10-20T00:00:00Z",
        )
        with patch("app.services.auth_service.AuthService.register_customer", return_value=mock_user):
            with patch("app.repositories.user_repo.UserRepository.get_user_role_names", return_value=["CUSTOMER"]):
                payload = {
                    "email": "api_test@novelia.vn",
                    "password": "Password123!",
                    "full_name": "API Reader",
                    "phone": "0901234567",
                }
                resp = client.post("/api/v1/auth/register", json=payload)
                assert resp.status_code == 201
                data = resp.json()
                assert data["email"] == "api_test@novelia.vn"
                assert data["roles"] == ["CUSTOMER"]

    def test_api_login_endpoint(self):
        """Verify POST /api/v1/auth/login handler."""
        mock_user = MagicMock(id=1, email="login_api@novelia.vn")
        with patch("app.services.auth_service.AuthService.authenticate", return_value=mock_user):
            with patch("app.repositories.user_repo.UserRepository.get_user_role_names", return_value=["CUSTOMER"]):
                payload = {
                    "email": "login_api@novelia.vn",
                    "password": "ValidPassword123!",
                }
                resp = client.post("/api/v1/auth/login", json=payload)
                assert resp.status_code == 200
                data = resp.json()
                assert "access_token" in data
                assert "refresh_token" in data
                assert data["token_type"] == "bearer"
                assert "CUSTOMER" in data["roles"]

    def test_api_me_without_token_unauthorized(self):
        """Verify GET /api/v1/users/me without Authorization header returns 401."""
        resp = client.get("/api/v1/users/me")
        assert resp.status_code == 401
        assert "not provided" in resp.json()["detail"].lower()

    def test_api_me_with_invalid_token_unauthorized(self):
        """Verify GET /api/v1/users/me with bogus token returns 401."""
        resp = client.get("/api/v1/users/me", headers={"Authorization": "Bearer invalid.token.payload"})
        assert resp.status_code == 401
        assert "invalid" in resp.json()["detail"].lower()
