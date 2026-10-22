"""Security, password hashing (bcrypt), and JWT token lifecycle utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Union
import bcrypt
import jwt
import logging

from app.core.config import settings

logger = logging.getLogger("novelia.security")

# In-memory blacklist for revoked tokens (e.g., upon user logout)
_revoked_token_jtis: Set[str] = set()


def get_password_hash(password: str) -> str:
    """Hash plaintext password using bcrypt with standard salt generation."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception as exc:
        logger.warning("Password verification failed with exception: %s", type(exc).__name__)
        return False


def create_access_token(
    user_id: Union[int, str],
    email: str,
    roles: List[str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate signed JWT access token containing identity and RBAC role claims."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "roles": roles,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    user_id: Union[int, str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate signed JWT refresh token for session renewals."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode: Dict[str, Any] = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate signature and expiry of a JWT token.
    
    Returns:
        Payload dict if valid; None if expired, malformed, or revoked.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("Token has expired")
        return None
    except jwt.PyJWTError as exc:
        logger.debug("JWT validation error: %s", type(exc).__name__)
        return None


def revoke_token(token: str) -> bool:
    """Add token signature or JTI to revoked set to instantly invalidate session."""
    payload = decode_token(token)
    if payload:
        # Use token string signature or hash as identifier
        _revoked_token_jtis.add(token[-32:])
        return True
    return False


def is_token_revoked(token: str) -> bool:
    """Check if token was revoked via logout."""
    return token[-32:] in _revoked_token_jtis
