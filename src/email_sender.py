"""
Email Sender Module
===================

LEARNING OBJECTIVE: Send emails programmatically via SMTP.

SMTP (Simple Mail Transfer Protocol) is how email gets delivered. When you
send from Gmail, Outlook, or any client, it uses SMTP under the hood. This
module uses Python's built-in smtplib - no external service required for
basic sending.

For GitHub Actions, you'll need to use either:
  - Gmail with an "App Password" (2FA required)
  - SendGrid, Mailgun, or similar (free tiers available)
  - Your own SMTP server

Environment variables used:
  - SMTP_HOST, SMTP_PORT: Server address
  - SMTP_USER, SMTP_PASSWORD: Credentials (use secrets in GitHub!)
  - NEWSLETTER_RECIPIENT: Your email address
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_newsletter(
    html_content: str,
    plain_text_content: str,
    subject: str = "Your Daily Newsletter",
) -> None:
    """
    Send the newsletter via SMTP.

    Uses multipart/alternative: email clients that support HTML get the pretty
    version; others get plain text. This is a best practice for HTML emails.
    """
    recipient = os.environ.get("NEWSLETTER_RECIPIENT")
    if not recipient:
        raise ValueError(
            "NEWSLETTER_RECIPIENT environment variable not set. "
            "Set it to your email address."
        )

    smtp_host = os.environ.get("SMTP_HOST") or "smtp.gmail.com"
    smtp_port = int(os.environ.get("SMTP_PORT") or "587")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        raise ValueError(
            "SMTP_USER and SMTP_PASSWORD must be set. "
            "For Gmail: use an App Password (not your regular password)."
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = recipient

    # Attach both versions - plain text first (lower preference), then HTML
    msg.attach(MIMEText(plain_text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()  # Upgrade to encrypted connection
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, recipient, msg.as_string())

    print(f"Newsletter sent successfully to {recipient}")
