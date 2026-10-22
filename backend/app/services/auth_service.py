"""Authentication domain service handling user registration, login, token issuance, and credential rotation."""

import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    is_token_revoked,
    revoke_token,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    ChangePasswordRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)

logger = logging.getLogger("novelia.auth")


class AuthService:
    """Service layer orchestrating identity, credentials, and session tokens."""

    @staticmethod
    def register_customer(db: Session, data: UserRegisterRequest) -> User:
        """Register a new customer account.
        
        Security Enforcement:
        - Prevents duplicate email accounts (HTTP 409).
        - Strictly assigns 'CUSTOMER' role; client cannot self-assign STAFF or ADMIN.
        - Hashes password using bcrypt prior to database insertion.
        """
        existing_user = UserRepository.get_by_email(db, data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered in the system",
            )

        hashed_pwd = get_password_hash(data.password)
        user = UserRepository.create_user(
            db=db,
            email=data.email,
            hashed_password=hashed_pwd,
            full_name=data.full_name,
            phone=data.phone,
        )

        # Enforce default retail customer role
        UserRepository.assign_role(db, user_id=user.id, role_name="CUSTOMER")
        db.commit()
        db.refresh(user)

        logger.info("New customer registered successfully: %s", user.email)
        return user

    @staticmethod
    def authenticate(db: Session, credentials: UserLoginRequest) -> User:
        """Authenticate user by email and password."""
        user = UserRepository.get_by_email(db, credentials.email)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(credentials.password, user.hashed_password):
            logger.warning("Failed login attempt for user: %s", credentials.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    @staticmethod
    def issue_tokens(user: User) -> TokenResponse:
        """Issue access and refresh token pair with encoded RBAC role claims."""
        roles = UserRepository.get_user_role_names(user)
        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            roles=roles,
        )
        refresh_token = create_refresh_token(user_id=user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            roles=roles,
        )

    @staticmethod
    def refresh_access_token(db: Session, refresh_token_str: str) -> TokenResponse:
        """Exchange a valid refresh token for a fresh token pair."""
        if is_token_revoked(refresh_token_str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = decode_token(refresh_token_str)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = int(payload.get("sub", 0))
        user = UserRepository.get_by_id(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Invalidate the old refresh token to prevent replay attacks
        revoke_token(refresh_token_str)
        return AuthService.issue_tokens(user)

    @staticmethod
    def change_password(
        db: Session,
        user: User,
        data: ChangePasswordRequest,
    ) -> None:
        """Change password with verification of old credentials."""
        if not verify_password(data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password does not match",
            )

        hashed_pwd = get_password_hash(data.new_password)
        UserRepository.update_password(db, user, hashed_pwd)
        db.commit()
        logger.info("Password changed successfully for user id: %d", user.id)

    @staticmethod
    def logout(token_str: str) -> None:
        """Revoke bearer token signature to immediately terminate active session."""
        revoke_token(token_str)
