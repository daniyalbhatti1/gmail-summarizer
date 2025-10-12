"""Send digest email via Gmail API."""

import base64
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytz

from .config import Config
from .gmail_client import GmailClient

logger = logging.getLogger(__name__)


def get_time_of_day() -> str:
    """Get time of day label (Morning or Mid-Day)."""
    now = datetime.now()
    if now.hour < 12:
        return "Morning"
    else:
        return "Mid-Day"


def create_message(
    to: str, subject: str, plaintext: str, html: str
) -> dict[str, str]:
    """
    Create a MIME multipart message with both plaintext and HTML.

    Args:
        to: Recipient email address
        subject: Email subject
        plaintext: Plaintext body
        html: HTML body

    Returns:
        Dictionary with base64url encoded 'raw' message
    """
    message = MIMEMultipart("alternative")
    message["To"] = to
    message["Subject"] = subject

    # Attach plaintext and HTML parts
    part1 = MIMEText(plaintext, "plain", "utf-8")
    part2 = MIMEText(html, "html", "utf-8")

    message.attach(part1)
    message.attach(part2)

    # Encode message
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    return {"raw": raw}


def send_digest(plaintext: str, html: str, config: Config) -> bool:
    """
    Send the digest email to the main email address.

    Args:
        plaintext: Plaintext body
        html: HTML body
        config: Application configuration

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        # Find the main email account in the configured accounts
        main_account = None
        for account in config.accounts:
            if account.email == config.main_email:
                main_account = account
                break

        if not main_account:
            # Use the first account if main email not in accounts
            logger.warning(
                f"Main email {config.main_email} not in configured accounts, using first account to send"
            )
            main_account = config.accounts[0]

        # Initialize client
        client = GmailClient(main_account, config.google_client_id, config.google_client_secret)

        # Create subject
        now = datetime.now(pytz.timezone(config.timezone))
        time_of_day = get_time_of_day()
        subject = f"Gmail Digest — {now.strftime('%Y-%m-%d')} — {time_of_day}"

        # Create message
        message = create_message(config.main_email, subject, plaintext, html)

        # Send
        result = client.send_message(message)

        if result:
            logger.info(f"Successfully sent digest to {config.main_email}")
            return True
        else:
            logger.error(f"Failed to send digest to {config.main_email}")
            return False

    except Exception as e:
        logger.error(f"Error sending digest: {e}")
        return False


def send_error_notification(error_message: str, config: Config) -> bool:
    """
    Send an error notification email.

    Args:
        error_message: The error message to send
        config: Application configuration

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        # Find the main email account
        main_account = None
        for account in config.accounts:
            if account.email == config.main_email:
                main_account = account
                break

        if not main_account:
            main_account = config.accounts[0]

        client = GmailClient(main_account, config.google_client_id, config.google_client_secret)

        # Create subject
        now = datetime.now(pytz.timezone(config.timezone))
        subject = f"Gmail Digest Error — {now.strftime('%Y-%m-%d %H:%M')}"

        # Create plaintext message
        plaintext = f"""Gmail Digest Error Notification

An error occurred while generating your Gmail digest:

{error_message}

Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}

Please check the logs for more details.

---
This is an automated notification from Gmail Digest.
"""

        # Create simple HTML message
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .error-box {{ background-color: #fee; border-left: 4px solid #c00; padding: 15px; margin: 20px 0; border-radius: 4px; }}
        .error-box h2 {{ margin-top: 0; color: #c00; }}
        .error-message {{ background-color: #fff; padding: 10px; border-radius: 4px; font-family: monospace; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <div class="error-box">
        <h2>⚠️ Gmail Digest Error</h2>
        <p>An error occurred while generating your Gmail digest:</p>
        <div class="error-message">{error_message}</div>
        <p><small>Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}</small></p>
    </div>
    <p>Please check the logs for more details.</p>
    <hr>
    <p><small>This is an automated notification from Gmail Digest.</small></p>
</body>
</html>"""

        # Create and send message
        message = create_message(config.main_email, subject, plaintext, html)
        result = client.send_message(message)

        if result:
            logger.info(f"Successfully sent error notification to {config.main_email}")
            return True
        else:
            logger.error(f"Failed to send error notification to {config.main_email}")
            return False

    except Exception as e:
        logger.error(f"Error sending error notification: {e}")
        return False

