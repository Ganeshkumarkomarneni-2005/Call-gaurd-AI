"""Email service for transactional notifications and password resets."""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import structlog

from backend.core.config import settings

logger: structlog.BoundLogger = structlog.get_logger(__name__)


async def send_password_reset_email(to_email: str, reset_token: str) -> dict:
    """Send or simulate a password reset email with the verification link.

    Args:
        to_email: Recipient email address.
        reset_token: Cryptographic reset token.

    Returns:
        Dict with dispatch status and details.
    """
    reset_link = f"{settings.frontend_url}/reset-password?token={reset_token}"
    subject = "CallGuard AI — Password Reset Request"

    text_body = f"""Hello,

We received a request to reset your password for your CallGuard AI account.

Click the link below to set a new password:
{reset_link}

This link will expire in 15 minutes. If you did not request this, you can safely ignore this email.

— The CallGuard AI Team
"""

    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 40px 20px;">
  <div style="max-width: 500px; margin: 0 auto; background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 32px;">
    <div style="display: flex; align-items: center; margin-bottom: 24px;">
      <h2 style="color: #38bdf8; margin: 0; font-size: 20px;">🛡️ CallGuard AI</h2>
    </div>
    <h3 style="color: #ffffff; margin-top: 0;">Password Reset Request</h3>
    <p style="color: #94a3b8; font-size: 14px; line-height: 1.6;">
      We received a request to reset your password. Click the button below to choose a new password. This link will expire in 15 minutes.
    </p>
    <div style="text-align: center; margin: 32px 0;">
      <a href="{reset_link}" style="background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-weight: 600; font-size: 14px; display: inline-block;">
        Reset Password
      </a>
    </div>
    <p style="color: #64748b; font-size: 12px; line-height: 1.5; word-break: break-all;">
      Or copy and paste this link into your browser:<br>
      <a href="{reset_link}" style="color: #38bdf8;">{reset_link}</a>
    </p>
    <hr style="border: 0; border-top: 1px solid #334155; margin: 24px 0;">
    <p style="color: #64748b; font-size: 11px;">
      If you did not request this password reset, please ignore this email.
    </p>
  </div>
</body>
</html>
"""

    # If SMTP is configured, send the real email
    if settings.smtp_host and settings.smtp_user and settings.smtp_password:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.smtp_from_email
            msg["To"] = to_email

            part1 = MIMEText(text_body, "plain")
            part2 = MIMEText(html_body, "html")
            msg.attach(part1)
            msg.attach(part2)

            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_from_email, to_email, msg.as_string())

            logger.info("Password reset email sent via SMTP", to_email=to_email)
            return {"status": "sent", "method": "smtp", "reset_link": reset_link}
        except Exception as exc:
            logger.error("Failed to send email via SMTP", error=str(exc), to_email=to_email)
            # Fall through to logged link

    # In local development or when SMTP is not configured:
    logger.info(
        "Password reset link generated (dev/console mode)",
        to_email=to_email,
        reset_link=reset_link,
    )
    return {"status": "dispatched", "method": "console", "reset_link": reset_link}
