"""Gmail API client wrapper with OAuth handling."""

import logging
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import AccountConfig

logger = logging.getLogger(__name__)


class GmailClient:
    """Wrapper for Gmail API with OAuth token management."""

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
    ]

    def __init__(self, account: AccountConfig, client_id: str, client_secret: str):
        """Initialize Gmail client for a specific account."""
        self.account = account
        self.client_id = client_id
        self.client_secret = client_secret
        self.service: Any = None
        self._initialize_service()

    def _initialize_service(self) -> None:
        """Initialize the Gmail API service with OAuth credentials."""
        try:
            # Create credentials from refresh token
            creds = Credentials(
                token=None,
                refresh_token=self.account.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=self.SCOPES,
            )

            # Refresh the token if needed
            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    raise ValueError(
                        f"Invalid credentials for {self.account.email}. "
                        "Please regenerate tokens using scripts/generate_tokens.py"
                    )

            # Build the service
            self.service = build("gmail", "v1", credentials=creds)
            logger.info(f"Successfully initialized Gmail client for {self.account.email}")

        except Exception as e:
            logger.error(f"Failed to initialize Gmail client for {self.account.email}: {e}")
            raise

    def list_messages(
        self, query: str, max_results: int = 500, page_token: str | None = None
    ) -> dict[str, Any]:
        """
        List messages matching the query.

        Args:
            query: Gmail search query
            max_results: Maximum number of results to return
            page_token: Token for pagination

        Returns:
            Dictionary with 'messages' and optional 'nextPageToken'
        """
        try:
            params: dict[str, Any] = {"userId": "me", "q": query, "maxResults": max_results}
            if page_token:
                params["pageToken"] = page_token

            result = self.service.users().messages().list(**params).execute()
            return result

        except HttpError as e:
            logger.error(f"Error listing messages for {self.account.email}: {e}")
            return {"messages": []}

    def get_message(self, message_id: str, format: str = "full") -> dict[str, Any] | None:
        """
        Get a specific message by ID.

        Args:
            message_id: The message ID
            format: Format of the message (full, metadata, minimal, raw)

        Returns:
            Message dictionary or None if not found
        """
        try:
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format=format)
                .execute()
            )
            return message

        except HttpError as e:
            logger.error(f"Error getting message {message_id} for {self.account.email}: {e}")
            return None

    def get_thread(self, thread_id: str, format: str = "full") -> dict[str, Any] | None:
        """
        Get a complete thread by ID.

        Args:
            thread_id: The thread ID
            format: Format of messages in the thread

        Returns:
            Thread dictionary or None if not found
        """
        try:
            thread = (
                self.service.users().threads().get(userId="me", id=thread_id, format=format).execute()
            )
            return thread

        except HttpError as e:
            logger.error(f"Error getting thread {thread_id} for {self.account.email}: {e}")
            return None

    def send_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        """
        Send an email message.

        Args:
            message: Message in RFC 2822 format (base64url encoded)

        Returns:
            Sent message dictionary or None on failure
        """
        try:
            sent = self.service.users().messages().send(userId="me", body=message).execute()
            logger.info(f"Successfully sent message from {self.account.email}")
            return sent

        except HttpError as e:
            logger.error(f"Error sending message from {self.account.email}: {e}")
            return None

    def get_profile(self) -> dict[str, Any] | None:
        """Get the user's Gmail profile."""
        try:
            profile = self.service.users().getProfile(userId="me").execute()
            return profile
        except HttpError as e:
            logger.error(f"Error getting profile for {self.account.email}: {e}")
            return None

