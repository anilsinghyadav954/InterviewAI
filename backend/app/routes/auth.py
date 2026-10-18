from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.schemas.user import UserProfileResponse, UserProfileUpdate
from app.services.auth_service import (
    register_user,
    authenticate_user,
    get_user_by_id,
    update_user_profile,
    request_password_reset,
    reset_password_with_token,
)
from app.utils.security import decode_access_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> dict:
    """FastAPI reusable dependency: Extracts Bearer token, validates JWT, returns user doc."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials or not credentials.credentials:
        raise credentials_exception

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    user = get_user_by_id(user_id)
    if not user:
        raise credentials_exception

    return user


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(request: RegisterRequest):
    return register_user(request)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and receive JWT token",
)
def login(request: LoginRequest):
    return authenticate_user(request)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.put(
    "/profile",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update candidate profile information",
)
def update_profile(
    update_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    return update_user_profile(current_user["id"], update_data)


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Request a secure, single-use password reset link via email",
)
def forgot_password(request_data: ForgotPasswordRequest, request: Request):
    client_ip = request.client.host if request.client else ""
    return request_password_reset(request_data.email, client_ip=client_ip)


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset candidate account password using valid reset token",
)
def reset_password(request_data: ResetPasswordRequest):
    return reset_password_with_token(request_data.token, request_data.new_password)
