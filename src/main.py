"""Main entry point for Gmail Digest."""

import logging
import sys
from datetime import datetime

import pytz

from .classify import classify_emails
from .config import get_config
from .fetch import fetch_all_accounts
from .render import render_digest
from .send import send_digest, send_error_notification
from .summarize import summarize

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def main() -> int:
    """
    Main function to orchestrate the Gmail digest pipeline.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        logger.info("=" * 70)
        logger.info("Gmail Digest - Starting")
        logger.info("=" * 70)

        # Load configuration
        logger.info("Loading configuration...")
        config = get_config()
        logger.info(f"Configured to monitor {len(config.accounts)} Gmail account(s)")
        logger.info(f"Digest will be sent to: {config.main_email}")
        logger.info(f"Looking back: {config.lookback_hours} hours")

        # Fetch emails from all accounts
        logger.info("Fetching emails from all accounts...")
        start_time = datetime.now()
        emails = fetch_all_accounts(config)
        fetch_duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Fetched {len(emails)} emails in {fetch_duration:.2f} seconds")

        if not emails:
            logger.info("No emails found. Skipping digest generation.")
            # Still send a brief notification
            plaintext = f"""Gmail Digest — {datetime.now(pytz.timezone(config.timezone)).strftime('%Y-%m-%d')}

No new emails found in the last {config.lookback_hours} hours.

All caught up! 🎉
"""
            html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
    <h2>📬 Gmail Digest</h2>
    <p>No new emails found in the last {config.lookback_hours} hours.</p>
    <p style="font-size: 48px;">🎉</p>
    <p><strong>All caught up!</strong></p>
</body>
</html>"""
            send_digest(plaintext, html, config)
            return 0

        # Classify emails
        logger.info("Classifying emails...")
        start_time = datetime.now()
        classified = classify_emails(emails, config)
        classify_duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Classified {len(classified)} emails (filtered {len(emails) - len(classified)} low-value) "
            f"in {classify_duration:.2f} seconds"
        )

        if not classified:
            logger.info("All emails were filtered as low-value. Skipping digest.")
            return 0

        # Generate summary
        logger.info("Generating summary...")
        summary = summarize(classified, config)

        # Render digest
        logger.info("Rendering digest...")
        plaintext, html = render_digest(summary, config)

        # Send digest
        logger.info("Sending digest...")
        success = send_digest(plaintext, html, config)

        if success:
            logger.info("=" * 70)
            logger.info("Gmail Digest - Completed Successfully")
            logger.info("=" * 70)
            return 0
        else:
            logger.error("Failed to send digest")
            return 1

    except Exception as e:
        error_message = f"Fatal error in Gmail Digest: {e}"
        logger.error(error_message, exc_info=True)

        # Try to send error notification
        try:
            config = get_config()
            send_error_notification(error_message, config)
        except Exception as notify_error:
            logger.error(f"Failed to send error notification: {notify_error}")

        return 1


if __name__ == "__main__":
    sys.exit(main())

