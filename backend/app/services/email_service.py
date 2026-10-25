import smtplib
import socket
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

# Test & development email capture queue (allows inspecting dispatched records safely)
_test_email_queue: List[Dict[str, Any]] = []


def get_test_email_queue() -> List[Dict[str, Any]]:
    """Returns test dispatched email records for testing purposes."""
    return _test_email_queue


def clear_test_email_queue() -> None:
    """Clears the test dispatched email records."""
    _test_email_queue.clear()


def build_reset_email_html(recipient_name: str, reset_url: str, reset_token: str = "", expires_in_minutes: int = 20) -> str:
    """Generates a responsive, branded HTML email for password reset."""
    display_name = recipient_name or "Candidate"
    token_display = f"""
      <div style="background-color: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 12px 16px; text-align: center; margin: 18px 0;">
        <span style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Your Single-Use Reset Code:</span><br>
        <code style="font-family: monospace; font-size: 13px; font-weight: 600; color: #4338ca; word-break: break-all;">{reset_token}</code>
      </div>
    """ if reset_token else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reset Your Password - InterviewAI</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b; }}
    .container {{ max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }}
    .header {{ background: linear-gradient(135deg, #4f46e5, #4338ca); padding: 32px 24px; text-align: center; color: #ffffff; }}
    .header h1 {{ margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.5px; }}
    .body {{ padding: 32px 28px; line-height: 1.6; font-size: 15px; color: #334155; }}
    .button-container {{ text-align: center; margin: 28px 0; }}
    .btn {{ display: inline-block; background-color: #4f46e5; color: #ffffff !important; text-decoration: none; padding: 14px 32px; border-radius: 10px; font-weight: 600; font-size: 15px; box-shadow: 0 2px 4px rgba(79, 70, 229, 0.25); }}
    .notice {{ background-color: #f1f5f9; border-left: 4px solid #6366f1; padding: 12px 16px; border-radius: 6px; font-size: 13px; color: #475569; margin: 24px 0; }}
    .footer {{ background-color: #f8fafc; padding: 20px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>InterviewAI</h1>
    </div>
    <div class="body">
      <p>Hello <strong>{display_name}</strong>,</p>
      <p>We received a request to reset the password for your InterviewAI candidate account.</p>
      <p>Click the button below to choose a new, secure password:</p>
      <div class="button-container">
        <a href="{reset_url}" class="btn" target="_blank" rel="noopener noreferrer">Reset Password</a>
      </div>
      {token_display}
      <div class="notice">
        <strong>Security Notice:</strong>
        <ul style="margin: 6px 0 0 0; padding-left: 20px;">
          <li>This link is strictly single-use and will expire in <strong>{expires_in_minutes} minutes</strong>.</li>
          <li>If you did not request a password reset, you can safely ignore this email. Your password will remain unchanged.</li>
          <li>Never share this reset link with anyone.</li>
        </ul>
      </div>
      <p style="font-size: 13px; color: #64748b; margin-top: 24px;">
        If the button above does not work, copy and paste this URL into your browser:<br>
        <span style="word-break: break-all; color: #4f46e5;">{reset_url}</span>
      </p>
    </div>
    <div class="footer">
      &copy; InterviewAI &bull; Automated Security Service &bull; Do not reply to this email
    </div>
  </div>
</body>
</html>
"""


def build_reset_email_text(recipient_name: str, reset_url: str, reset_token: str = "", expires_in_minutes: int = 20) -> str:
    """Generates plain text fallback email."""
    display_name = recipient_name or "Candidate"
    token_section = f"\nYour Single-Use Reset Code:\n{reset_token}\n" if reset_token else ""
    return f"""Hello {display_name},

We received a request to reset the password for your InterviewAI candidate account.

To reset your password, visit the link below:
{reset_url}
{token_section}
Security Notice:
- This link is single-use and expires in {expires_in_minutes} minutes.
- If you did not request this, you can safely ignore this message. Your password remains unchanged.
- Never share this link or code with anyone.

--
InterviewAI Security Team
"""


def send_password_reset_email(to_email: str, recipient_name: str, reset_token: str) -> bool:
    """
    Dispatches password reset email.
    - If valid SMTP settings are configured (host, username, password), delivers via real SMTP using STARTTLS.
    - If SMTP settings are missing or contain placeholder values, logs development simulation safely.
    - Captures safe dispatch record in _test_email_queue for local testing inspection.
    - NEVER logs SMTP_PASSWORD or the raw reset_token to application logs.
    """
    reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={reset_token}"
    html_content = build_reset_email_html(recipient_name, reset_url, reset_token=reset_token, expires_in_minutes=20)
    text_content = build_reset_email_text(recipient_name, reset_url, reset_token=reset_token, expires_in_minutes=20)

    # In development or testing environment, capture dispatch in test queue safely
    _test_email_queue.append({
        "to_email": to_email,
        "recipient_name": recipient_name,
        "reset_token": reset_token,
        "reset_url": reset_url,
    })

    # Check whether real SMTP delivery is configured
    if not settings.is_smtp_configured:
        logger.info(
            f"SMTP server not configured or placeholder credentials detected. "
            f"Password reset email simulated in development mode for recipient '{to_email}'."
        )
        return True

    # Real Live SMTP Delivery (e.g. Gmail STARTTLS on port 587)
    username = settings.effective_smtp_username
    from_email = settings.effective_smtp_from_email
    from_name = settings.SMTP_FROM_NAME or "InterviewAI"

    server: Optional[smtplib.SMTP] = None
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Reset Your Password - InterviewAI"
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = to_email

        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        # Connect to SMTP host and port
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20)
        server.ehlo()

        if settings.SMTP_USE_TLS:
            server.starttls()
            server.ehlo()

        if username and settings.SMTP_PASSWORD:
            server.login(username, settings.SMTP_PASSWORD)

        server.send_message(msg)
        logger.info(f"Password reset email successfully dispatched via SMTP to '{to_email}'.")
        return True

    except smtplib.SMTPAuthenticationError as e:
        # Never print SMTP_PASSWORD in logs
        logger.error(
            f"SMTP authentication failed for user '{username}': Please verify your Gmail address "
            f"and 16-character App Password (code: {e.smtp_code})."
        )
        return False
    except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, ConnectionRefusedError, socket.timeout, TimeoutError, OSError) as e:
        logger.error(
            f"Failed to connect to SMTP server '{settings.SMTP_HOST}:{settings.SMTP_PORT}': {type(e).__name__}."
        )
        return False
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"SMTP server rejected recipient address '{to_email}': {e}.")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP protocol error while sending reset email to '{to_email}': {type(e).__name__}.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while sending email via SMTP: {type(e).__name__}.")
        return False
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass
