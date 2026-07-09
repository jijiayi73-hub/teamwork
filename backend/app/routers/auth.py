from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..auth.security import create_access_token, hash_password, verify_password
from ..config import settings
from ..database import get_db
from ..models import User
from ..schemas.auth import (
    TokenRead,
    UserCreate,
    UserLogin,
    UserRead,
    PasswordResetRequest,
    PasswordResetVerify,
    PasswordResetConfirm,
    PasswordResetVerifyResponse,
    PasswordResetResponse,
)
from ..schemas.common import ApiResponse
from ..services.password_reset_service import get_password_reset_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=ApiResponse[TokenRead], status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(or_(User.email == payload.email, User.username == payload.username)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username or email already exists")
    user = User(
        username=payload.username,
        email=str(payload.email),
        password_hash=hash_password(payload.password),
        role=payload.role if payload.role in {"user", "admin"} else "user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(str(user.id), user.role)
    return ApiResponse(data=TokenRead(access_token=token, user=user), message="registered")


@router.post("/login", response_model=ApiResponse[TokenRead])
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        or_(User.username == payload.username_or_email, User.email == payload.username_or_email)
    ).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username, email or password")
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    token = create_access_token(str(user.id), user.role)
    return ApiResponse(data=TokenRead(access_token=token, user=user), message="logged_in")


@router.get("/me", response_model=ApiResponse[UserRead])
def me(user: User = Depends(get_current_user)):
    return ApiResponse(data=user)


# Password reset endpoints
@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(
    payload: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Request a password reset email.

    This endpoint always returns 202 to prevent email enumeration attacks.
    The actual email will be sent if the account exists.
    """
    # Get base URL from request or use default
    base_url = str(request.base_url).rstrip("/")

    service = get_password_reset_service(db)
    service.request_password_reset(str(payload.email), base_url)

    return ApiResponse(
        data={"message": "如果该邮箱已注册，您将收到密码重置邮件"},
        message="password_reset_requested",
    )


@router.post("/password-reset/verify", response_model=ApiResponse[PasswordResetVerifyResponse])
def verify_reset_token(payload: PasswordResetVerify, db: Session = Depends(get_db)):
    """Verify a password reset token is valid and not expired."""
    service = get_password_reset_service(db)
    result = service.verify_token(payload.token)

    return ApiResponse(
        data=PasswordResetVerifyResponse(
            valid=result["valid"],
            email_partial=result.get("email_partial"),
            error=result.get("error"),
        ),
        message="token_verified" if result["valid"] else "token_invalid",
    )


@router.post("/password-reset/confirm", response_model=ApiResponse[PasswordResetResponse])
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Confirm password reset and set new password."""
    service = get_password_reset_service(db)
    result = service.reset_password(payload.token, payload.new_password)

    response_data = PasswordResetResponse(success=result["success"], error=result.get("error"))

    if not result["success"]:
        # Return appropriate HTTP status based on error
        error = result.get("error")
        if error == "invalid_token" or error == "expired_token":
            raise HTTPException(status_code=400, detail=result.get("error"))
        elif error == "password_too_short":
            raise HTTPException(
                status_code=422,
                detail="new_password must be at least 6 characters",
            )

    return ApiResponse(data=response_data, message="password_reset" if result["success"] else "reset_failed")
