from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional


import re

def validate_strong_password(v: str) -> str:
    cleaned = v.strip()
    if len(cleaned) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", cleaned):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", cleaned):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", cleaned):
        raise ValueError("Password must contain at least one number.")
    return v


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, description="Password with minimum 8 characters")
    confirm_password: str = Field(..., description="Password confirmation")

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Full name cannot be empty")
        return cleaned

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        return validate_strong_password(v)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Password confirmation must match password")
        return v


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=1, description="Password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class AuthResponseUser(BaseModel):
    id: str
    full_name: str
    email: str


class RegisterResponse(BaseModel):
    message: str = "Registration successful"
    user: AuthResponseUser


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthResponseUser


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered account email")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class ForgotPasswordResponse(BaseModel):
    message: str = "If an account exists for this email, a password reset link has been sent."


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1, description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password with minimum 8 characters")
    confirm_new_password: Optional[str] = None

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Reset token is required")
        return cleaned

    @field_validator("new_password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        return validate_strong_password(v)

    @field_validator("confirm_new_password")
    @classmethod
    def passwords_match(cls, v: Optional[str], info) -> Optional[str]:
        if v is not None and "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Password confirmation must match new password")
        return v


class ResetPasswordResponse(BaseModel):
    message: str = "Password has been reset successfully. You can now log in with your new password."
