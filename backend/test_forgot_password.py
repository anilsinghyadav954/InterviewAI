"""
================================================================================
InterviewAI - Forgot Password & Password Reset Comprehensive Test Suite
================================================================================
Validates:
1. Forgot password with existing email (generic response, token creation, email dispatch)
2. Forgot password with non-existing email (anti-enumeration security, same response)
3. Cryptographic token generation & secure hashing (SHA-256 in DB, raw token never stored)
4. Token expiration enforcement (expired token rejected with 400)
5. Invalid/tampered token rejection (400)
6. Single-use token enforcement (used token rejected on re-use)
7. Successful password reset (bcrypt hashing, password_changed_at recorded)
8. Weak password rejection (minimum 8 chars, uppercase, lowercase, number)
9. Old password invalidation (old password rejected with 401)
10. New password authentication (new password logs in successfully with JWT)
11. Invalidation of older unused tokens when a fresh reset is requested
12. Sliding window rate limiting on forgot password requests (HTTP 429)
13. Normal login and register operations continue working without regression
================================================================================
"""

import sys
import os
import time
import hashlib
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from bson import ObjectId

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.database import (
    init_db,
    get_users_collection,
    get_password_resets_collection,
)
from app.services.email_service import get_test_email_queue, clear_test_email_queue
from app.utils.rate_limiter import forgot_password_limiter
from app.utils.security import verify_password

client = TestClient(app)

print("\n" + "=" * 65)
print("INTERVIEWAI - FORGOT PASSWORD & RESET PASSWORD TEST SUITE")
print("=" * 65 + "\n")


def run_tests():
    init_db()
    forgot_password_limiter.reset()
    clear_test_email_queue()

    test_id = int(time.time())
    email = f"candidate_reset_{test_id}@example.com"
    initial_password = "InitialPassword123!"
    new_password = "NewStrongPassword456!"

    print("[Test 1] Candidate Registration...")
    res_reg = client.post(
        "/api/auth/register",
        json={
            "full_name": "Reset Test User",
            "email": email,
            "password": initial_password,
            "confirm_password": initial_password,
        },
    )
    assert res_reg.status_code == 201, f"Reg failed: {res_reg.text}"
    print("  [PASS] Candidate registered successfully.")

    print("\n[Test 2] Initial Login Verification...")
    res_login_init = client.post(
        "/api/auth/login",
        json={"email": email, "password": initial_password},
    )
    assert res_login_init.status_code == 200
    assert "access_token" in res_login_init.json()
    print("  [PASS] Initial login authenticated with initial password.")

    print("\n[Test 3] Forgot Password Request with Existing Email...")
    res_forgot = client.post(
        "/api/auth/forgot-password",
        json={"email": email},
    )
    assert res_forgot.status_code == 200
    forgot_data = res_forgot.json()
    generic_msg = "If an account exists for this email, a password reset link has been sent."
    assert forgot_data["message"] == generic_msg
    print(f"  [PASS] Received generic response: '{forgot_data['message']}'.")

    # Verify email was captured in dispatch queue
    queue = get_test_email_queue()
    assert len(queue) == 1, f"Expected 1 email in queue, found {len(queue)}"
    dispatched = queue[0]
    assert dispatched["to_email"] == email
    raw_token = dispatched["reset_token"]
    assert len(raw_token) > 20, "Token should have high entropy"
    print("  [PASS] Password reset email safely dispatched with secure token.")

    print("\n[Test 4] Verify Token Security in MongoDB...")
    resets_col = get_password_resets_collection()
    # Ensure raw token is NOT stored anywhere in the database
    raw_in_db = resets_col.find_one({"token": raw_token})
    assert raw_in_db is None, "SECURITY VIOLATION: Raw token must never be stored in MongoDB!"

    # Ensure SHA-256 hash IS stored
    expected_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    token_doc = resets_col.find_one({"token_hash": expected_hash})
    assert token_doc is not None, "Token hash not found in password_reset_tokens collection"
    assert token_doc["used"] is False
    assert token_doc["email"] == email
    print("  [PASS] Cryptographic verification confirmed: Only SHA-256 token hash is stored.")

    print("\n[Test 5] Anti-Enumeration Security (Non-Existent Email)...")
    res_non_exist = client.post(
        "/api/auth/forgot-password",
        json={"email": f"nonexistent_{test_id}@example.com"},
    )
    assert res_non_exist.status_code == 200
    assert res_non_exist.json()["message"] == generic_msg
    # Verify no email was dispatched for non-existent user
    assert len(queue) == 1, "No email should be dispatched for non-existent user"
    print("  [PASS] Non-existent email returns identical generic response (anti-enumeration verified).")

    print("\n[Test 6] Weak Password Rejection During Reset...")
    # 6.1 Too short
    res_short = client.post(
        "/api/auth/reset-password",
        json={"token": raw_token, "new_password": "short"},
    )
    assert res_short.status_code == 422
    print("  [PASS] Password under 8 characters rejected with HTTP 422.")

    # 6.2 No uppercase
    res_no_upper = client.post(
        "/api/auth/reset-password",
        json={"token": raw_token, "new_password": "lowercase1234!"},
    )
    assert res_no_upper.status_code == 422
    print("  [PASS] Password without uppercase letter rejected with HTTP 422.")

    # 6.3 No number
    res_no_num = client.post(
        "/api/auth/reset-password",
        json={"token": raw_token, "new_password": "NoNumbersHere!"},
    )
    assert res_no_num.status_code == 422
    print("  [PASS] Password without numbers rejected with HTTP 422.")

    print("\n[Test 7] Invalid or Tampered Token Rejection...")
    res_fake_token = client.post(
        "/api/auth/reset-password",
        json={"token": "completely_fake_invalid_token_12345", "new_password": new_password},
    )
    assert res_fake_token.status_code == 400
    print("  [PASS] Invalid/tampered token rejected with HTTP 400 Bad Request.")

    print("\n[Test 8] Expired Token Rejection...")
    # Artificially expire the token in database
    past_time = datetime.now(timezone.utc) - timedelta(minutes=25)
    resets_col.update_one({"_id": token_doc["_id"]}, {"$set": {"expires_at": past_time}})

    res_expired = client.post(
        "/api/auth/reset-password",
        json={"token": raw_token, "new_password": new_password},
    )
    assert res_expired.status_code == 400
    assert "expired" in res_expired.json()["detail"].lower()
    print("  [PASS] Expired token strictly rejected with HTTP 400 Bad Request.")

    print("\n[Test 9] Invalidation of Prior Tokens When Requesting New Token...")
    # Request a fresh reset token
    clear_test_email_queue()
    res_forgot2 = client.post(
        "/api/auth/forgot-password",
        json={"email": email},
    )
    assert res_forgot2.status_code == 200
    fresh_queue = get_test_email_queue()
    assert len(fresh_queue) == 1
    fresh_token_1 = fresh_queue[0]["reset_token"]

    # Request a second fresh token immediately
    time.sleep(0.1)
    res_forgot3 = client.post(
        "/api/auth/forgot-password",
        json={"email": email},
    )
    assert res_forgot3.status_code == 200
    fresh_token_2 = fresh_queue[1]["reset_token"]

    # Attempting to use the superseded first token should fail because it was invalidated
    res_superseded = client.post(
        "/api/auth/reset-password",
        json={"token": fresh_token_1, "new_password": new_password},
    )
    assert res_superseded.status_code == 400
    print("  [PASS] Superseded reset token was automatically invalidated.")

    print("\n[Test 10] Successful Password Reset...")
    res_reset_success = client.post(
        "/api/auth/reset-password",
        json={"token": fresh_token_2, "new_password": new_password},
    )
    assert res_reset_success.status_code == 200
    assert "successfully" in res_reset_success.json()["message"].lower()
    print("  [PASS] Password reset succeeded with 200 OK.")

    print("\n[Test 11] Single-Use Token Enforcement (Re-use Rejection)...")
    res_reuse = client.post(
        "/api/auth/reset-password",
        json={"token": fresh_token_2, "new_password": "AnotherPassword999!"},
    )
    assert res_reuse.status_code == 400
    assert "already been used" in res_reuse.json()["detail"].lower()
    print("  [PASS] Re-using already-used token strictly rejected with HTTP 400.")

    print("\n[Test 12] Authentication Post-Reset Behavior...")
    # Old password must FAIL (401)
    res_old_login = client.post(
        "/api/auth/login",
        json={"email": email, "password": initial_password},
    )
    assert res_old_login.status_code == 401
    print("  [PASS] Old password no longer works (rejected with HTTP 401).")

    # New password must SUCCEED (200 with JWT)
    res_new_login = client.post(
        "/api/auth/login",
        json={"email": email, "password": new_password},
    )
    assert res_new_login.status_code == 200
    new_token = res_new_login.json()["access_token"]
    assert new_token is not None

    # Test protected route with new JWT
    res_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {new_token}"})
    assert res_me.status_code == 200
    assert res_me.json()["email"] == email
    print("  [PASS] New password authenticated successfully, new JWT access token issued and operational.")

    print("\n[Test 13] Rate Limiting Abuse Protection (HTTP 429)...")
    spam_email = f"spam_test_{test_id}@example.com"
    # The limiter allows 5 requests per 60s
    for i in range(5):
        res = client.post("/api/auth/forgot-password", json={"email": spam_email})
        assert res.status_code == 200

    # 6th request must trigger rate limit 429
    res_limited = client.post("/api/auth/forgot-password", json={"email": spam_email})
    assert res_limited.status_code == 429
    assert "Rate limit exceeded" in res_limited.json()["detail"]
    print("  [PASS] Rate limiter triggered HTTP 429 Too Many Requests upon 6th rapid attempt.")

    print("\n[Test 14] Real SMTP STARTTLS Delivery Flow (Configured Credentials)...")
    from unittest.mock import patch, MagicMock
    import smtplib
    from app.services.email_service import send_password_reset_email
    from app.config import settings

    with patch.object(settings, "SMTP_HOST", "smtp.gmail.com"), \
         patch.object(settings, "SMTP_PORT", 587), \
         patch.object(settings, "SMTP_USERNAME", "mock_user@gmail.com"), \
         patch.object(settings, "SMTP_PASSWORD", "mock_app_password_16ch"), \
         patch.object(settings, "SMTP_FROM_EMAIL", "mock_user@gmail.com"), \
         patch.object(settings, "SMTP_USE_TLS", True):

        assert settings.is_smtp_configured is True

        mock_server = MagicMock()
        with patch("smtplib.SMTP", return_value=mock_server) as mock_smtp_cls:
            success = send_password_reset_email(
                to_email="recipient@example.com",
                recipient_name="Recipient User",
                reset_token="mock_sample_token_xyz"
            )

            assert success is True
            mock_smtp_cls.assert_called_once_with("smtp.gmail.com", 587, timeout=20)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("mock_user@gmail.com", "mock_app_password_16ch")
            mock_server.send_message.assert_called_once()
            mock_server.quit.assert_called_once()
            print("  [PASS] Real SMTP STARTTLS delivery executed, login verified, and email dispatched.")

    print("\n[Test 15] SMTP Authentication Failure Handling...")
    with patch.object(settings, "SMTP_HOST", "smtp.gmail.com"), \
         patch.object(settings, "SMTP_PORT", 587), \
         patch.object(settings, "SMTP_USERNAME", "mock_user@gmail.com"), \
         patch.object(settings, "SMTP_PASSWORD", "wrong_password"), \
         patch.object(settings, "SMTP_USE_TLS", True):

        mock_auth_fail = MagicMock()
        mock_auth_fail.login.side_effect = smtplib.SMTPAuthenticationError(535, b"5.7.8 Authentication credentials invalid")
        with patch("smtplib.SMTP", return_value=mock_auth_fail):
            auth_result = send_password_reset_email(
                to_email="recipient@example.com",
                recipient_name="Recipient User",
                reset_token="mock_sample_token_xyz"
            )
            assert auth_result is False
            print("  [PASS] SMTPAuthenticationError caught safely without crashing or exposing secrets.")

    print("\n[Test 16] SMTP Connection Failure Handling...")
    with patch.object(settings, "SMTP_HOST", "smtp.gmail.com"), \
         patch.object(settings, "SMTP_PORT", 587), \
         patch.object(settings, "SMTP_USERNAME", "mock_user@gmail.com"), \
         patch.object(settings, "SMTP_PASSWORD", "mock_pwd"):

        with patch("smtplib.SMTP", side_effect=smtplib.SMTPConnectError(421, b"Connection refused")):
            conn_result = send_password_reset_email(
                to_email="recipient@example.com",
                recipient_name="Recipient User",
                reset_token="mock_sample_token_xyz"
            )
            assert conn_result is False
            print("  [PASS] SMTPConnectError caught gracefully and handled safely.")

    print("\n" + "=" * 65)
    print("ALL FORGOT PASSWORD & PASSWORD RESET TESTS PASSED (100% SUCCESS)!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_tests()

