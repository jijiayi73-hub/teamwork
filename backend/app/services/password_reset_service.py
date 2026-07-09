"""Password reset service for managing password reset tokens and flow."""

from __future__ import annotations

import secrets
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from ..models import User
from ..auth.security import hash_password
from .email_service import get_email_service

logger = logging.getLogger(__name__)


class PasswordResetService:
    """Service for handling password reset operations."""

    # Token expiration time (30 minutes)
    TOKEN_EXPIRY_MINUTES = 30

    def __init__(self, db: Session) -> None:
        self.db = db
        self.email_service = get_email_service()

    def generate_token(self) -> str:
        """Generate a secure random token.

        Returns:
            URL-safe base64-encoded random token
        """
        # Generate 32 bytes (256 bits) of random data and encode as base64
        token_bytes = secrets.token_bytes(32)
        return secrets.token_urlsafe(32)

    def request_password_reset(self, email: str, base_url: str) -> bool:
        """Request a password reset for the given email.

        Args:
            email: User's email address
            base_url: Base URL for constructing reset link (e.g., http://localhost:5173)

        Returns:
            True if request was processed (email sent if user exists)
        Note:
            Always returns True to prevent email enumeration attacks.
        """
        # Find user by email
        user = self.db.query(User).filter(User.email == email).first()

        if not user:
            # User doesn't exist - don't reveal this but log it
            logger.info(f"Password reset requested for non-existent email: {email}")
            return True

        if user.status != "active":
            # Inactive user - don't reveal this
            logger.info(f"Password reset requested for inactive user: {email}")
            return True

        # Generate token
        token = self.generate_token()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.TOKEN_EXPIRY_MINUTES)

        # Store token in database
        user.reset_token = token
        user.reset_token_expires_at = expires_at
        self.db.commit()

        # Send email
        reset_link = f"{base_url}/#/password-reset?token={token}"
        email_sent = self.email_service.send_password_reset_email(
            to_email=email,
            username=user.username,
            reset_link=reset_link,
        )

        if email_sent:
            logger.info(f"Password reset email sent to: {email}")
        else:
            logger.error(f"Failed to send password reset email to: {email}")

        return True

    def verify_token(self, token: str) -> dict:
        """Verify a password reset token.

        Args:
            token: The reset token to verify

        Returns:
            Dict with 'valid' bool and optionally 'user_id' and 'email_partial'
        """
        if not token:
            return {"valid": False, "error": "missing_token"}

        user = self.db.query(User).filter(User.reset_token == token).first()

        if not user:
            return {"valid": False, "error": "invalid_token"}

        if user.reset_token_expires_at is None:
            return {"valid": False, "error": "invalid_token"}

        if datetime.now(timezone.utc) > user.reset_token_expires_at:
            # Token expired - clear it
            user.reset_token = None
            user.reset_token_expires_at = None
            self.db.commit()
            return {"valid": False, "error": "expired_token"}

        return {
            "valid": True,
            "user_id": user.id,
            "email_partial": self._mask_email(user.email),
        }

    def reset_password(self, token: str, new_password: str) -> dict:
        """Reset user's password using token.

        Args:
            token: The reset token
            new_password: New password to set

        Returns:
            Dict with 'success' bool and optionally 'error'
        """
        if not token:
            return {"success": False, "error": "missing_token"}

        if not new_password or len(new_password) < 6:
            return {"success": False, "error": "password_too_short"}

        # Verify token
        verification = self.verify_token(token)
        if not verification["valid"]:
            return {"success": False, "error": verification.get("error", "invalid_token")}

        # Get user
        user = self.db.query(User).filter(User.reset_token == token).first()

        if not user:
            return {"success": False, "error": "invalid_token"}

        # Update password
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)

        # Clear the reset token (one-time use)
        user.reset_token = None
        user.reset_token_expires_at = None

        self.db.commit()

        logger.info(f"Password reset successfully for user: {user.email}")

        return {"success": True}

    def _mask_email(self, email: str) -> str:
        """Mask email for privacy (e.g., j***@example.com).

        Args:
            email: Email to mask

        Returns:
            Masked email string
        """
        if "@" not in email:
            return email

        local, domain = email.split("@", 1)
        if len(local) > 1:
            masked_local = local[0] + "***" + local[-1] if len(local) > 2 else local[0] + "***"
        else:
            masked_local = "***"

        return f"{masked_local}@{domain}"


def get_password_reset_service(db: Session) -> PasswordResetService:
    """Factory function to get password reset service instance."""
    return PasswordResetService(db)
