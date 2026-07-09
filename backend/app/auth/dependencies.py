from __future__ import annotations

import logging
from typing import Union

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import (
    DecodeError,
    ExpiredSignatureError,
    ImmatureSignatureError,
    InvalidAlgorithmError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidKeyError,
    InvalidSignatureError,
    InvalidTokenError,
    MissingRequiredClaimError,
)
from sqlalchemy.orm import Session

from ..database import get_db
from ..logger import get_logger
from ..models import User
from .security import decode_access_token

bearer_scheme = HTTPBearer()
logger = get_logger(__name__)


def _get_token_error_detail(exc: Exception) -> str:
    """
    将 JWT 异常转换为用户友好的错误消息。
    注意：不泄露敏感的内部实现细节。
    """
    if isinstance(exc, ExpiredSignatureError):
        return "Token has expired. Please log in again."
    if isinstance(exc, (DecodeError, InvalidSignatureError)):
        return "Invalid token format."
    if isinstance(exc, ImmatureSignatureError):
        return "Token not yet valid."
    if isinstance(exc, InvalidAlgorithmError):
        return "Token algorithm not supported."
    if isinstance(exc, (InvalidAudienceError, InvalidIssuerError)):
        return "Token validation failed."
    if isinstance(exc, MissingRequiredClaimError):
        return "Token missing required information."
    if isinstance(exc, InvalidKeyError):
        return "Token key validation failed."
    # 默认消息，保持通用以避免信息泄露
    return "Invalid token"


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except Exception as e:
        # 记录详细的错误信息用于调试，但不返回给用户
        error_type = type(e).__name__
        error_detail = _get_token_error_detail(e)
        logger.warning(
            "token_validation_failed",
            error_type=error_type,
            error_message=str(e),
            user_detail=error_detail,
            # 不记录完整的 token 内容
            token_prefix=token[:10] if len(token) > 10 else token,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_detail,
        ) from e

    user = db.get(User, user_id)
    if not user or user.status != "active":
        logger.warning(
            "user_not_found_or_inactive",
            user_id=user_id,
            user_exists=user is not None,
            user_status=user.status if user else None,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        logger.warning("admin_required", user_id=user.id, user_role=user.role)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user
