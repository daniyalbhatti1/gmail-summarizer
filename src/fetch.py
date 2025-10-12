
"""Fetch and expand email messages from Gmail."""

import base64
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any

import pytz

from .config import Config
from .gmail_client import GmailClient

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """Structured representation of an email message."""

    message_id: str
    thread_id: str
    account_email: str
    subject: str
    sender: str
    sender_email: str
    recipients: list[str]
    date: datetime
    snippet: str
    body_text: str
    body_html: str
    labels: list[str]
    has_attachments: bool
    is_reply: bool
    headers: dict[str, str]
    raw_message: dict[str, Any]


def build_search_query(config: Config) -> str:
    """
    Build an optimized Gmail search query.

    Filters out:
    - Promotional/social/forum categories
    - Spam
    - Common noise patterns
    - Messages older than lookback_hours
    """
    # Calculate the time threshold
    days_back = max(1, config.lookback_hours // 24)

    # Base query components
    query_parts = [
        "in:inbox",
        f"newer_than:{days_back}d",
        "-category:{promotions social forums}",
        "-label:spam",
        "-from:mailer-daemon",
        "-subject:undeliverable",
    ]

    return " ".join(query_parts)


def extract_header(headers: list[dict[str, str]], name: str) -> str:
    """Extract a header value by name (case-insensitive)."""
    name_lower = name.lower()
    for header in headers:
        if header.get("name", "").lower() == name_lower:
            return header.get("value", "")
    return ""


def extract_email_address(email_string: str) -> str:
    """Extract email address from 'Name <email@domain.com>' format."""
    import re

    match = re.search(r"<(.+?)>", email_string)
    if match:
        return match.group(1)
    return email_string.strip()


def decode_body(data: str) -> str:
    """Decode base64url encoded body content."""
    try:
        # Gmail uses base64url encoding (- and _ instead of + and /)
        decoded_bytes = base64.urlsafe_b64decode(data)
        return decoded_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        logger.warning(f"Failed to decode body: {e}")
        return ""


def extract_body_parts(payload: dict[str, Any]) -> tuple[str, str]:
    """
    Extract text and HTML body parts from message payload.

    Returns:
        Tuple of (text_body, html_body)
    """
    text_body = ""
    html_body = ""

    def extract_from_parts(parts: list[dict[str, Any]]) -> None:
        nonlocal text_body, html_body
        for part in parts:
            mime_type = part.get("mimeType", "")
            if mime_type == "text/plain":
                body_data = part.get("body", {}).get("data", "")
                if body_data and not text_body:
                    text_body = decode_body(body_data)
            elif mime_type == "text/html":
                body_data = part.get("body", {}).get("data", "")
                if body_data and not html_body:
                    html_body = decode_body(body_data)
            elif mime_type.startswith("multipart/"):
                # Recursively process multipart
                sub_parts = part.get("parts", [])
                if sub_parts:
                    extract_from_parts(sub_parts)

    # Check if single part message
    mime_type = payload.get("mimeType", "")
    if mime_type == "text/plain":
        body_data = payload.get("body", {}).get("data", "")
        if body_data:
            text_body = decode_body(body_data)
    elif mime_type == "text/html":
        body_data = payload.get("body", {}).get("data", "")
        if body_data:
            html_body = decode_body(body_data)
    elif mime_type.startswith("multipart/"):
        parts = payload.get("parts", [])
        extract_from_parts(parts)

    return text_body, html_body


def check_attachments(payload: dict[str, Any]) -> bool:
    """Check if message has attachments."""

    def has_attachment_in_parts(parts: list[dict[str, Any]]) -> bool:
        for part in parts:
            if part.get("filename"):
                return True
            sub_parts = part.get("parts", [])
            if sub_parts and has_attachment_in_parts(sub_parts):
                return True
        return False

    parts = payload.get("parts", [])
    return has_attachment_in_parts(parts)


def parse_message(
    raw_message: dict[str, Any], account_email: str, config: Config
) -> EmailMessage | None:
    """
    Parse a raw Gmail message into structured EmailMessage.

    Args:
        raw_message: Raw message from Gmail API
        account_email: The account this message belongs to
        config: Application configuration

    Returns:
        EmailMessage or None if parsing fails
    """
    try:
        message_id = raw_message.get("id", "")
        thread_id = raw_message.get("threadId", "")
        snippet = raw_message.get("snippet", "")
        labels = raw_message.get("labelIds", [])

        payload = raw_message.get("payload", {})
        headers_list = payload.get("headers", [])

        # Extract headers
        headers = {h["name"]: h["value"] for h in headers_list}
        subject = extract_header(headers_list, "Subject")
        sender = extract_header(headers_list, "From")
        sender_email = extract_email_address(sender)
        to_header = extract_header(headers_list, "To")
        recipients = [extract_email_address(r.strip()) for r in to_header.split(",") if r.strip()]

        # Parse date
        date_str = extract_header(headers_list, "Date")
        try:
            date = parsedate_to_datetime(date_str)
            # Convert to configured timezone
            tz = pytz.timezone(config.timezone)
            if date.tzinfo is None:
                date = pytz.utc.localize(date)
            date = date.astimezone(tz)
        except Exception:
            date = datetime.now(pytz.timezone(config.timezone))

        # Extract body
        text_body, html_body = extract_body_parts(payload)

        # Check for attachments
        has_attachments = check_attachments(payload)

        # Check if it's a reply
        in_reply_to = extract_header(headers_list, "In-Reply-To")
        references = extract_header(headers_list, "References")
        is_reply = bool(in_reply_to or references)

        return EmailMessage(
            message_id=message_id,
            thread_id=thread_id,
            account_email=account_email,
            subject=subject,
            sender=sender,
            sender_email=sender_email,
            recipients=recipients,
            date=date,
            snippet=snippet,
            body_text=text_body or snippet,
            body_html=html_body,
            labels=labels,
            has_attachments=has_attachments,
            is_reply=is_reply,
            headers=headers,
            raw_message=raw_message,
        )

    except Exception as e:
        logger.error(f"Failed to parse message: {e}")
        return None


def fetch_messages(
    client: GmailClient, config: Config, max_results: int = 500
) -> list[EmailMessage]:
    """
    Fetch messages from a Gmail account.

    Args:
        client: Initialized Gmail client
        config: Application configuration
        max_results: Maximum number of messages to fetch

    Returns:
        List of parsed EmailMessage objects
    """
    logger.info(f"Fetching messages for {client.account.email}")

    query = build_search_query(config)
    logger.debug(f"Search query: {query}")

    messages: list[EmailMessage] = []
    seen_thread_ids: set[str] = set()

    try:
        # Fetch message IDs
        result = client.list_messages(query=query, max_results=max_results)
        message_list = result.get("messages", [])

        logger.info(f"Found {len(message_list)} message IDs for {client.account.email}")

        # Fetch full messages (dedupe by thread)
        for msg_ref in message_list:
            message_id = msg_ref["id"]

            # Get full message
            raw_message = client.get_message(message_id, format="full")
            if not raw_message:
                continue

            thread_id = raw_message.get("threadId", "")

            # Skip if we've already processed this thread
            if thread_id in seen_thread_ids:
                continue

            seen_thread_ids.add(thread_id)

            # Parse message
            parsed = parse_message(raw_message, client.account.email, config)
            if parsed:
                messages.append(parsed)

        logger.info(f"Successfully fetched {len(messages)} unique threads for {client.account.email}")

    except Exception as e:
        logger.error(f"Error fetching messages for {client.account.email}: {e}")

    return messages


def fetch_all_accounts(config: Config) -> list[EmailMessage]:
    """
    Fetch messages from all configured Gmail accounts.

    Args:
        config: Application configuration

    Returns:
        Combined list of messages from all accounts
    """
    all_messages: list[EmailMessage] = []

    for account in config.accounts:
        try:
            client = GmailClient(account, config.google_client_id, config.google_client_secret)
            messages = fetch_messages(client, config)
            all_messages.extend(messages)
        except Exception as e:
            logger.error(f"Failed to fetch from {account.email}: {e}")
            continue

    logger.info(f"Total messages fetched from all accounts: {len(all_messages)}")
    return all_messages

