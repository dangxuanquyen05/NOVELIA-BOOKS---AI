"""Authentication Pydantic schemas for registration, login, token refresh, and password management."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """Registration payload for new customers. Role escalation is strictly prohibited."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72, description="Password between 8 and 72 characters")
    full_name: str = Field(..., min_length=2, max_length=150)
    phone: Optional[str] = Field(None, max_length=20)


class UserLoginRequest(BaseModel):
    """Credentials payload for authentication."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Bearer access and refresh token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    roles: List[str]


class RefreshTokenRequest(BaseModel):
    """Payload to exchange valid refresh token for a new access token."""

    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Payload to update password with verification of existing password."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=72)


class MessageResponse(BaseModel):
    """Standard generic operational response."""

    message: str
    status: str = "success"
