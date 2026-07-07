"""
Data sanitization utilities for secure logging.

Removes or masks sensitive data before logging.
"""

from typing import Any, Set

# Fields that should never be logged
SENSITIVE_FIELDS = {
    "password",
    "api_key",
    "token",
    "secret",
    "access_token",
    "refresh_token",
    "private_key",
    "authorization",
    "bearer",
    "credentials",
    "pin",
    "ssn",
    "social_security_number",
}


def sanitize_dict(data: dict, fields_to_hide: Set[str] | None = None) -> dict:
    """Recursively sanitize a dictionary by hiding sensitive fields.

    Args:
        data: The dictionary to sanitize
        fields_to_hide: Specific fields to hide (uses SENSITIVE_FIELDS if None)

    Returns:
        A new dictionary with sensitive fields masked
    """
    if fields_to_hide is None:
        fields_to_hide = SENSITIVE_FIELDS

    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        key_lower = key.lower()
        if key_lower in fields_to_hide or any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
            # Completely hide sensitive fields
            result[key] = "***"
        elif isinstance(value, dict):
            # Recursively sanitize nested dictionaries
            result[key] = sanitize_dict(value, fields_to_hide)
        elif isinstance(value, list):
            # Recursively sanitize items in lists
            result[key] = [
                sanitize_dict(item, fields_to_hide) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result


def sanitize_url(url: str) -> str:
    """Remove sensitive query parameters from URLs.

    Args:
        url: The URL to sanitize

    Returns:
        A sanitized URL with sensitive parameters removed
    """
    from urllib.parse import urlparse, parse_qs, urlunparse

    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)

        # Remove sensitive parameters
        sanitized_params = {}
        for key, values in query_params.items():
            if key.lower() not in SENSITIVE_FIELDS and not any(
                sensitive in key.lower() for sensitive in SENSITIVE_FIELDS
            ):
                sanitized_params[key] = values

        # Rebuild URL
        sanitized = parsed._replace(
            query="&".join(f"{k}={v}" for k, vals in sanitized_params.items() for v in vals)
        )
        return urlunparse(sanitized)
    except Exception:
        # If URL parsing fails, return original
        return url


def mask_email(email: str) -> str:
    """Mask an email address for logging.

    Args:
        email: The email to mask

    Returns:
        A masked email like "u***@example.com"
    """
    try:
        if "@" not in email:
            return email
        local, domain = email.split("@", 1)
        if len(local) <= 1:
            return f"*{local}@{domain}"
        return f"{local[0]}***@{domain}"
    except Exception:
        return "***@***.***"


def mask_string(s: str, keep_chars: int = 4) -> str:
    """Mask a string, keeping only the first and last few characters.

    Args:
        s: The string to mask
        keep_chars: Number of characters to keep at each end

    Returns:
        A masked string like "test***test"
    """
    if not s or len(s) <= keep_chars * 2:
        return "***" * len(s) if s else "***"

    if len(s) <= keep_chars * 2:
        return s[:keep_chars] + "***"

    return f"{s[:keep_chars]}***{s[-keep_chars:]}"


def mask_phone(phone: str) -> str:
    """Mask a phone number for logging.

    Args:
        phone: The phone number to mask

    Returns:
        A masked phone like "(***) ***-****"
    """
    if not phone:
        return "***"

    # Keep area code only if available
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) >= 10:
        return f"(***) ***-****-{digits[-4:]}"
    return "(***) ***-****"
