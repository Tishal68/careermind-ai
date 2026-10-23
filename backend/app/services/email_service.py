import logging
import smtplib
from email.message import EmailMessage
from typing import Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)

# Test outbox for capturing generated emails in tests
test_outbox: List[Dict[str, Any]] = []


def is_smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_HOST.strip())


def send_email(to_email: str, subject: str, content: str) -> Dict[str, Any]:
    """
    Delivers an email via configured SMTP server.
    If SMTP is not configured, records the attempt in test_outbox (if in test/dev)
    and returns an explicit unconfigured status. Never simulates success.
    """
    if not is_smtp_configured():
        logger.warning(
            f"Email delivery skipped for {to_email}: SMTP_HOST is not configured."
        )
        record = {
            "to": to_email,
            "subject": subject,
            "content": content,
            "delivered": False,
            "reason": "SMTP host is not configured on this server.",
        }
        test_outbox.append(record)
        return record

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg.set_content(content)

    try:
        if settings.SMTP_TLS:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(
                        settings.SMTP_USER,
                        settings.SMTP_PASSWORD.get_secret_value(),
                    )
                server.send_message(msg)
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(
                        settings.SMTP_USER,
                        settings.SMTP_PASSWORD.get_secret_value(),
                    )
                server.send_message(msg)

        logger.info(f"Email successfully delivered to {to_email}")
        return {"delivered": True, "to": to_email}
    except Exception as exc:
        logger.error(f"Failed to deliver email to {to_email}: {exc}")
        return {"delivered": False, "to": to_email, "reason": str(exc)}


def send_password_reset_email(to_email: str, token: str) -> Dict[str, Any]:
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    subject = "CareerMind AI - Password Reset Request"
    body = (
        f"Hello,\n\n"
        f"A password reset was requested for your CareerMind AI account.\n\n"
        f"You can reset your password by opening the following link:\n"
        f"{reset_url}\n\n"
        f"This link expires in 15 minutes and can only be used once.\n"
        f"If you did not request this, you can safely ignore this email.\n\n"
        f"- The CareerMind AI Team"
    )
    return send_email(to_email, subject, body)


def send_verification_email(to_email: str, token: str) -> Dict[str, Any]:
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    subject = "CareerMind AI - Verify Your Email Address"
    body = (
        f"Hello,\n\n"
        f"Thank you for registering with CareerMind AI.\n\n"
        f"Please verify your email address by opening the following link:\n"
        f"{verify_url}\n\n"
        f"This link expires in 24 hours and can only be used once.\n\n"
        f"- The CareerMind AI Team"
    )
    return send_email(to_email, subject, body)
