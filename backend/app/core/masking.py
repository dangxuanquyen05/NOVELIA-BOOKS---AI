"""Sensitive data masking utility for audit logging and privacy governance.

Ensures credentials, access tokens, passwords, and sensitive financial secrets
are never persisted in plain text in audit logs, system event logs, or AI traces.
"""

import copy
from typing import Any, Dict, List, Set, Union

SENSITIVE_FIELD_NAMES: Set[str] = {
    "password",
    "password_hash",
    "hashed_password",
    "old_password",
    "new_password",
    "confirm_password",
    "token",
    "access_token",
    "refresh_token",
    "auth_token",
    "secret",
    "secret_key",
    "api_key",
    "gemini_api_key",
    "smtp_password",
    "cvv",
    "card_number",
    "pin",
    "authorization",
    "cookie",
    "session_secret",
}

REDACTED_PLACEHOLDER = "***REDACTED***"


def mask_sensitive_data(
    data: Any,
    sensitive_keys: Set[str] = SENSITIVE_FIELD_NAMES,
    mask_placeholder: str = REDACTED_PLACEHOLDER,
) -> Any:
    """Recursively mask sensitive keys in nested dictionaries, lists, and primitives.

    Args:
        data: The arbitrary input object (dict, list, primitive, or None).
        sensitive_keys: Set of lowercase key names to redact.
        mask_placeholder: The replacement string for redacted values.

    Returns:
        A deep-copied and sanitized data structure with sensitive values replaced.
    """
    if data is None:
        return None

    if isinstance(data, dict):
        sanitized: Dict[str, Any] = {}
        for key, value in data.items():
            key_lower = str(key).lower().strip()
            if any(sens in key_lower for sens in sensitive_keys):
                sanitized[key] = mask_placeholder
            elif isinstance(value, (dict, list)):
                sanitized[key] = mask_sensitive_data(
                    value, sensitive_keys, mask_placeholder
                )
            else:
                sanitized[key] = value
        return sanitized

    if isinstance(data, list):
        return [
            mask_sensitive_data(item, sensitive_keys, mask_placeholder)
            for item in data
        ]

    return data
