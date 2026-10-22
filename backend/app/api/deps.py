"""Dependency injection providers for database sessions, current authenticated user, and RBAC enforcement."""

from typing import Callable, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token, is_token_revoked
from app.database.connection import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository

# Use HTTPBearer for standard Bearer token header extraction
security_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
) -> User:
    """Validate bearer token and resolve authenticated User entity."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or malformed authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = UserRepository.get_by_id(db, int(user_id_str))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Guarantees current user is active."""
    return current_user


def get_current_user_optional(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
) -> User | None:
    """Optional authentication: returns User if valid bearer token provided, else None."""
    if not credentials or not credentials.credentials:
        return None

    token = credentials.credentials
    if is_token_revoked(token):
        return None

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None

    user_id_str = payload.get("sub")
    if not user_id_str:
        return None

    try:
        user = UserRepository.get_by_id(db, int(user_id_str))
        if user and user.is_active:
            return user
    except Exception:
        return None

    return None


def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    """Factory creating dependency to enforce RBAC permissions (CUSTOMER, STAFF, ADMIN).
    
    Admins automatically inherit access across all protected routes.
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        user_roles = UserRepository.get_user_role_names(current_user)
        # ADMIN role has superuser privileges across system endpoints
        if "ADMIN" in user_roles:
            return current_user

        if not any(role in allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker
