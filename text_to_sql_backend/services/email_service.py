"""Minimal SMTP email sending - currently only used for password-reset links."""
from __future__ import annotations

import smtplib
from email.message import EmailMessage

from config.settings import settings


def send_password_reset_email(to_email: str, reset_link: str) -> None:
    """Send a password-reset email over SMTP (STARTTLS). Raises on failure -
    callers decide whether/how to surface that to the user."""
    message = EmailMessage()
    message["Subject"] = "Reset your PG AI Assistant password"
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = to_email
    message.set_content(
        "You requested a password reset for PG AI Assistant.\n\n"
        f"Reset your password using this link (valid for {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes):\n"
        f"{reset_link}\n\n"
        "If you didn't request this, you can safely ignore this email."
    )
    message.add_alternative(
        f"""\
<html>
  <body style="font-family: sans-serif;">
    <p>You requested a password reset for <strong>PG AI Assistant</strong>.</p>
    <p><a href="{reset_link}">Click here to reset your password</a>
    (valid for {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes).</p>
    <p>If you didn't request this, you can safely ignore this email.</p>
  </body>
</html>
""",
        subtype="html",
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        smtp.starttls()
        smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)
