"""
Test email validation with development domains.

Tests that .local, .localhost, .test domains are allowed for demo environments.
"""
import pytest
from pydantic import ValidationError

from app.schemas.auth import UserCreate, UserLogin
from app.schemas.common import DevelopmentEmailStr, validate_email_with_local_domains


class TestEmailValidation:
    """Test custom email validator allows development domains."""

    def test_validate_email_with_local_domains(self):
        """Test direct validator function with .local domains."""
        # Should allow .local domains
        assert validate_email_with_local_domains("demo@innergarden.local") == "demo@innergarden.local"
        assert validate_email_with_local_domains("user@example.local") == "user@example.local"
        assert validate_email_with_local_domains("admin@app.localhost") == "admin@app.localhost"

    def test_validate_email_with_test_domains(self):
        """Test .test and .example domains are allowed."""
        assert validate_email_with_local_domains("user@example.test") == "user@example.test"
        assert validate_email_with_local_domains("demo@app.example") == "demo@app.example"

    def test_validate_email_normal_domains(self):
        """Test normal email domains still work."""
        assert validate_email_with_local_domains("user@gmail.com") == "user@gmail.com"
        assert validate_email_with_local_domains("admin@outlook.com") == "admin@outlook.com"

    def test_validate_email_invalid_format(self):
        """Test invalid email formats are rejected."""
        with pytest.raises(ValueError, match="An email address must have an @-sign"):
            validate_email_with_local_domains("not-an-email")

        # Standard validator gives different error for edge cases
        with pytest.raises(ValueError):
            validate_email_with_local_domains("@invalid.com")

        with pytest.raises(ValueError, match="An email address must have an @-sign"):
            validate_email_with_local_domains("no-at-sign.com")

    def test_user_create_with_local_domain(self):
        """Test UserCreate schema accepts .local domains."""
        user = UserCreate(
            username="demo",
            email="demo@innergarden.local",
            password="password123"
        )
        assert user.email == "demo@innergarden.local"

    def test_user_create_normalizes_email(self):
        """Test email is normalized to lowercase."""
        user = UserCreate(
            username="demo",
            email="DEMO@InnerGarden.Local",
            password="password123"
        )
        assert user.email == "demo@innergarden.local"

    def test_user_login_with_local_domain(self):
        """Test UserLogin schema accepts .local domains."""
        login = UserLogin(
            email="user@innergarden.local",
            password="password123"
        )
        assert login.email == "user@innergarden.local"

    def test_user_create_rejects_invalid_format(self):
        """Test UserCreate rejects invalid email format."""
        with pytest.raises(ValidationError):
            UserCreate(
                username="demo",
                email="not-an-email",
                password="password123"
            )
