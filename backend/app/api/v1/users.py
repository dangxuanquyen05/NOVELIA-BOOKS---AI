"""User profile and RBAC authorization endpoints."""

from typing import Dict
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db, require_roles
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserProfileUpdateRequest, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users & Profiles"])


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
def get_my_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Retrieve identity and permissions of the currently authenticated account."""
    roles = UserRepository.get_user_role_names(current_user)
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        is_active=current_user.is_active,
        roles=roles,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.put(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update profile details",
)
def update_my_profile(
    data: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Update editable profile fields for current user."""
    updated = UserService.update_profile(db, current_user, data)
    roles = UserRepository.get_user_role_names(updated)
    return UserResponse(
        id=updated.id,
        email=updated.email,
        full_name=updated.full_name,
        phone=updated.phone,
        is_active=updated.is_active,
        roles=roles,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


# -------------------------------------------------------------
# RBAC Validation Endpoints
# -------------------------------------------------------------
@router.get(
    "/rbac/staff-zone",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Restricted endpoint requiring STAFF or ADMIN role",
)
def staff_protected_zone(
    current_user: User = Depends(require_roles("STAFF")),
) -> Dict[str, str]:
    """Protected operation accessible only by STAFF or ADMIN users."""
    return {
        "status": "authorized",
        "message": f"Welcome to staff operational zone, {current_user.full_name}",
        "user_email": current_user.email,
    }


@router.get(
    "/rbac/admin-zone",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Restricted endpoint strictly requiring ADMIN role",
)
def admin_protected_zone(
    current_user: User = Depends(require_roles("ADMIN")),
) -> Dict[str, str]:
    """Protected operation accessible strictly by ADMIN users."""
    return {
        "status": "authorized",
        "message": f"Welcome to executive admin zone, {current_user.full_name}",
        "user_email": current_user.email,
    }
