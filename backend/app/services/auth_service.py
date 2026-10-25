import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.database import get_users_collection, get_password_resets_collection
from app.schemas.auth import RegisterRequest, LoginRequest
from app.schemas.user import UserProfileUpdate
from app.utils.security import hash_password, verify_password, create_access_token
from app.services.email_service import send_password_reset_email
from app.utils.rate_limiter import forgot_password_limiter


def doc_to_user_dict(doc: dict) -> dict:
    """Helper to convert MongoDB doc with ObjectId to safe API dict."""
    if not doc:
        return None
    return {
        "id": str(doc["_id"]),
        "full_name": doc.get("full_name", ""),
        "email": doc.get("email", ""),
        "college": doc.get("college", "Stanford University"),
        "degree": doc.get("degree", "Bachelor of Science"),
        "branch": doc.get("branch", "Computer Science & Engineering"),
        "graduation_year": doc.get("graduation_year", "2025"),
        "skills": doc.get("skills", ["JavaScript", "TypeScript", "React", "Node.js", "Python", "Tailwind CSS"]),
        "target_role": doc.get("target_role", "Full Stack Developer"),
        "profile_image": doc.get("profile_image", None),
    }


def register_user(req: RegisterRequest) -> dict:
    """Registers a new candidate in MongoDB after hashing the password."""
    users = get_users_collection()
    normalized_email = req.email.strip().lower()

    # Check for existing email
    existing = users.find_one({"email": normalized_email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Securely hash password
    hashed_pwd = hash_password(req.password)
    now = datetime.now(timezone.utc)

    user_doc = {
        "full_name": req.full_name.strip(),
        "email": normalized_email,
        "password_hash": hashed_pwd,
        "college": "Stanford University",
        "degree": "Bachelor of Science",
        "branch": "Computer Science & Engineering",
        "graduation_year": "2025",
        "skills": [
            "JavaScript",
            "TypeScript",
            "React",
            "Node.js",
            "Python",
            "Tailwind CSS",
        ],
        "target_role": "Full Stack Developer",
        "profile_image": None,
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = users.insert_one(user_doc)
        user_id = str(result.inserted_id)
        return {
            "message": "Registration successful",
            "user": {
                "id": user_id,
                "full_name": user_doc["full_name"],
                "email": user_doc["email"],
            },
        }
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )


def authenticate_user(req: LoginRequest) -> dict:
    """Validates candidate credentials and generates signed JWT token."""
    users = get_users_collection()
    normalized_email = req.email.strip().lower()

    user = users.find_one({"email": normalized_email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password hash
    if not verify_password(req.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT token
    user_id = str(user["_id"])
    token_payload = {
        "sub": user_id,
        "email": user["email"],
        "name": user["full_name"],
    }
    access_token = create_access_token(data=token_payload)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "full_name": user["full_name"],
            "email": user["email"],
        },
    }


def get_user_by_id(user_id: str) -> dict:
    """Finds user by ObjectId string."""
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None

    users = get_users_collection()
    user = users.find_one({"_id": oid})
    return doc_to_user_dict(user)


def update_user_profile(user_id: str, update_data: UserProfileUpdate) -> dict:
    """Updates candidate profile fields in MongoDB."""
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )

    users = get_users_collection()
    update_dict = {
        k: v for k, v in update_data.model_dump().items() if v is not None
    }
    if not update_dict:
        user = users.find_one({"_id": oid})
        return doc_to_user_dict(user)

    update_dict["updated_at"] = datetime.now(timezone.utc)
    users.update_one({"_id": oid}, {"$set": update_dict})

    updated_user = users.find_one({"_id": oid})
    return doc_to_user_dict(updated_user)


def request_password_reset(email: str, client_ip: str = "") -> dict:
    """
    Handles candidate forgot password request.
    1. Checks rate limiter on (client_ip or email) to prevent abuse.
    2. Looks up user by normalized email.
    3. If user exists:
       - Generates cryptographically secure token using secrets.token_urlsafe(32)
       - Computes SHA-256 hash of token
       - Invalidates prior unused tokens for this user
       - Stores token_hash, user_id, expires_at (20 mins), used=False in password_reset_tokens
       - Dispatches email via email_service
    4. If user does NOT exist:
       - Returns the exact same response to prevent user account enumeration.
    """
    normalized_email = email.strip().lower()
    # Rate limit check by email and IP
    rate_key = f"{client_ip}:{normalized_email}" if client_ip else normalized_email
    forgot_password_limiter.check_rate_limit(rate_key)

    users = get_users_collection()
    user = users.find_one({"email": normalized_email})

    if user:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=20)

        resets_col = get_password_resets_collection()
        # Invalidate any prior unused reset tokens for this user
        resets_col.update_many(
            {"user_id": user["_id"], "used": False},
            {"$set": {"used": True, "invalidated": True, "invalidated_at": now}}
        )

        # Store secure hash of token
        resets_col.insert_one({
            "user_id": user["_id"],
            "email": normalized_email,
            "token_hash": token_hash,
            "expires_at": expires_at,
            "used": False,
            "used_at": None,
            "created_at": now,
        })

        # Send password reset email
        send_password_reset_email(
            to_email=normalized_email,
            recipient_name=user.get("full_name", ""),
            reset_token=raw_token,
        )

    return {
        "message": "If an account exists for this email, a password reset link has been sent."
    }


def reset_password_with_token(token: str, new_password: str) -> dict:
    """
    Validates reset token and updates candidate password.
    1. Hashes received token and looks up in password_reset_tokens.
    2. Validates token is not expired and has not been used.
    3. Hashes new password using existing bcrypt implementation.
    4. Updates user password_hash in MongoDB and marks token as used.
    """
    cleaned_token = token.strip()
    if not cleaned_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token cannot be empty.",
        )

    token_hash = hashlib.sha256(cleaned_token.encode("utf-8")).hexdigest()
    resets_col = get_password_resets_collection()
    token_doc = resets_col.find_one({"token_hash": token_hash})

    if not token_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )

    if token_doc.get("used"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link has already been used. Please request a new one.",
        )

    now = datetime.now(timezone.utc)
    expires_at = token_doc.get("expires_at")
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at and expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link has expired. Please request a new one.",
        )

    users = get_users_collection()
    user_id = token_doc.get("user_id")
    user = users.find_one({"_id": user_id})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User associated with this reset link was not found.",
        )

    # Hash new password using project's standard bcrypt implementation
    hashed_pwd = hash_password(new_password)

    # Update candidate password and timestamp
    users.update_one(
        {"_id": user_id},
        {"$set": {
            "password_hash": hashed_pwd,
            "password_changed_at": now,
            "updated_at": now,
        }}
    )

    # Mark this token as used so it cannot be reused
    resets_col.update_one(
        {"_id": token_doc["_id"]},
        {"$set": {"used": True, "used_at": now}}
    )

    # Invalidate any other active tokens for this user
    resets_col.update_many(
        {"user_id": user_id, "used": False},
        {"$set": {"used": True, "invalidated": True, "invalidated_at": now}}
    )

    return {
        "message": "Password has been reset successfully. You can now log in with your new password."
    }
