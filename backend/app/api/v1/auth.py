"""Authentication API routes: Registration, Login, Token Refresh, Logout, and Password Change."""

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    ChangePasswordRequest,
    MessageResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication & Access"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new customer account",
)
def register(
    data: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Register a new customer account.
    
    Security: Always registers as CUSTOMER. Role escalation is forbidden.
    """
    user = AuthService.register_customer(db, data)
    roles = UserRepository.get_user_role_names(user)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        is_active=user.is_active,
        roles=roles,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate with email and password",
)
def login(
    credentials: UserLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Verify credentials and issue signed JWT access & refresh token pair."""
    user = AuthService.authenticate(db, credentials)
    return AuthService.issue_tokens(user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh expired access token",
)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Submit valid refresh token to obtain a fresh token pair."""
    return AuthService.refresh_access_token(db, payload.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke active session token",
)
def logout(
    authorization: str = Header(..., description="Bearer token"),
) -> MessageResponse:
    """Invalidate current bearer token signature."""
    token = authorization.replace("Bearer ", "").strip()
    AuthService.logout(token)
    return MessageResponse(message="Successfully logged out and session revoked")


@router.post(
    "/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Change user account password",
)
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Change password for authenticated user with verification of current password."""
    AuthService.change_password(db, current_user, data)
    return MessageResponse(message="Password updated successfully")
