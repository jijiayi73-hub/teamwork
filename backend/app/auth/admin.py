"""
Admin authentication dependencies.

Provides dependency functions for admin-only endpoints.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from .dependencies import get_current_user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current authenticated user and verify they have admin role.

    Raises:
        HTTPException: If the user is not an admin

    Returns:
        User: The authenticated admin user
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. You do not have permission to access this resource.",
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Alias for get_current_admin for semantic clarity.

    This is used when you want to explicitly require admin access
    in the dependency chain.
    """
    return await get_current_admin(current_user)
