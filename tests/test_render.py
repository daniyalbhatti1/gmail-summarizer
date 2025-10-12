"""Tests for email rendering."""

from datetime import datetime

import pytest
import pytz

from src.classify import ClassifiedEmail, Priority
from src.config import Config
from src.fetch import EmailMessage
from src.render import format_date, get_gmail_link, render_digest, render_html, render_plaintext
from src.summarize import summarize


@pytest.fixture
def mock_config() -> Config:
    """Create a mock configuration for testing."""
    return Config(
        main_email="main@gmail.com",
        accounts=[],
        google_client_id="test_client_id",
        google_client_secret="test_client_secret",
        openai_api_key=None,
        use_llm=False,
        timezone="America/New_York",
        lookback_hours=48,
        whitelist_senders=[],
        blacklist_senders=[],
        urgent_subject_patterns=[],
        ignore_subject_patterns=[],
        important_body_keywords=[],
        ignore_labels=[],
        scoring={},
        thresholds={"drop": 0, "fyi": 2, "actionable": 5, "urgent": 8},
    )


@pytest.fixture
def sample_classified_emails() -> list[ClassifiedEmail]:
    """Create sample classified emails for testing."""
    tz = pytz.timezone("America/New_York")
    now = datetime.now(tz)

    emails = []

    # Urgent email
    email1 = EmailMessage(
        message_id="msg1",
        thread_id="thread1",
        account_email="test@gmail.com",
        subject="URGENT: Server down",
        sender="Alert <alert@company.com>",
        sender_email="alert@company.com",
        recipients=["test@gmail.com"],
        date=now,
        snippet="Production server is down",
        body_text="Immediate action required",
        body_html="",
        labels=["INBOX", "IMPORTANT"],
        has_attachments=False,
        is_reply=False,
        headers={},
        raw_message={},
    )
    classified1 = ClassifiedEmail(
        email=email1,
        priority=Priority.URGENT,
        score=15,
        tags=["urgent-subject", "important-label"],
        gist="Production server is down",
        reasoning="High score and urgent indicators",
    )
    emails.append(classified1)

    # Meeting email
    email2 = EmailMessage(
        message_id="msg2",
        thread_id="thread2",
        account_email="test@gmail.com",
        subject="Meeting: Q4 Planning",
        sender="Boss <boss@company.com>",
        sender_email="boss@company.com",
        recipients=["test@gmail.com"],
        date=now,
        snippet="Join us for Q4 planning",
        body_text="Meeting on Friday at 2pm",
        body_html="",
        labels=["INBOX"],
        has_attachments=False,
        is_reply=False,
        headers={},
        raw_message={},
    )
    classified2 = ClassifiedEmail(
        email=email2,
        priority=Priority.MEETING,
        score=8,
        tags=["calendar-invite"],
        gist="Join us for Q4 planning",
        reasoning="Calendar invite detected",
    )
    emails.append(classified2)

    # Actionable email
    email3 = EmailMessage(
        message_id="msg3",
        thread_id="thread3",
        account_email="test@gmail.com",
        subject="Please review PR #123",
        sender="Colleague <colleague@company.com>",
        sender_email="colleague@company.com",
        recipients=["test@gmail.com"],
        date=now,
        snippet="Your review is needed",
        body_text="Please review when you have time",
        body_html="",
        labels=["INBOX"],
        has_attachments=True,
        is_reply=True,
        headers={},
        raw_message={},
    )
    classified3 = ClassifiedEmail(
        email=email3,
        priority=Priority.ACTIONABLE,
        score=6,
        tags=["reply-chain", "has-attachment"],
        gist="Your review is needed",
        reasoning="Actionable request",
    )
    emails.append(classified3)

    return emails


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_format_date(self) -> None:
        """Test date formatting."""
        tz = pytz.timezone("America/New_York")
        dt = datetime(2025, 10, 11, 14, 30, 0, tzinfo=tz)
        formatted = format_date(dt)

        assert "October" in formatted
        assert "2025" in formatted
        assert "02:30 PM" in formatted or "14:30" in formatted

    def test_get_gmail_link(self, sample_classified_emails: list[ClassifiedEmail]) -> None:
        """Test Gmail link generation."""
        email = sample_classified_emails[0]
        link = get_gmail_link(email)

        assert link.startswith("https://mail.google.com/mail/u/0/#all/")
        assert email.email.thread_id in link


class TestPlaintextRender:
    """Tests for plaintext rendering."""

    def test_plaintext_render_structure(
        self, mock_config: Config, sample_classified_emails: list[ClassifiedEmail]
    ) -> None:
        """Test that plaintext render has correct structure."""
        summary = summarize(sample_classified_emails, mock_config)
        plaintext = render_plaintext(summary, mock_config)

        # Check for key sections
        assert "Gmail Digest" in plaintext
        assert "AT A GLANCE" in plaintext
        assert "URGENT" in plaintext
        assert "MEETING" in plaintext
        assert "ACTION ITEMS" in plaintext

    def test_plaintext_includes_email_details(
        self, mock_config: Config, sample_classified_emails: list[ClassifiedEmail]
    ) -> None:
        """Test that plaintext includes email details."""
        summary = summarize(sample_classified_emails, mock_config)
        plaintext = render_plaintext(summary, mock_config)

        # Check for email subjects
        assert "URGENT: Server down" in plaintext
        assert "Meeting: Q4 Planning" in plaintext
        assert "Please review PR #123" in plaintext

        # Check for senders
        assert "alert@company.com" in plaintext
        assert "boss@company.com" in plaintext

    def test_plaintext_includes_footer(
        self, mock_config: Config, sample_classified_emails: list[ClassifiedEmail]
    ) -> None:
        """Test that plaintext includes configuration tips."""
        summary = summarize(sample_classified_emails, mock_config)
        plaintext = render_plaintext(summary, mock_config)

        assert "Configuration Tips" in plaintext
        assert "config.yml" in plaintext


class TestHTMLRender:
    """Tests for HTML rendering."""

    def test_html_render_valid(
        self, mock_config: Config, sample_classified_emails: list[ClassifiedEmail]
    ) -> None:
        """Test that HTML render is valid HTML."""
        summary = summarize(sample_classified_emails, mock_config)
        html = render_html(summary, mock_config)

        # Check for HTML structure
        assert html.startswith("<!DOCTYPE html>")
        assert "<html" in html
        assert "</html>" in html
        assert "<body" in html
        assert "</body>" in html

    def test_html_includes_styles(
        self, mock_config: Config, sample_classified_emails: list[ClassifiedEmail]
    ) -> None:
        """Test that HTML includes CSS styles."""
        summary = summarize(sample_classified_emails, mock_config)
        html = render_html(summary, mock_config)

        assert "<style>" in html
        assert "</style>" in html
        assert "font-family" in html

    def test_html_includes_email_details(
        self, mock_config: Config, sample_classified_emails: list[ClassifiedEmail]
    ) -> None:
        """Test that HTML includes email details."""
        summary = summarize(sample_classified_emails, mock_config)
        html = render_html(summary, mock_config)

        # Check for email subjects (HTML escaped)
        assert "URGENT: Server down" in html
        assert "Meeting: Q4 Planning" in html
        assert "Please review PR #123" in html

    def test_html_includes_links(
        self, mock_config: Config, sample_classified_emails: list[ClassifiedEmail]
    ) -> None:
        """Test that HTML includes Gmail links."""
        summary = summarize(sample_classified_emails, mock_config)
        html = render_html(summary, mock_config)

        assert "https://mail.google.com/mail/u/0/#all/" in html
        assert 'target="_blank"' in html

    def test_html_includes_sections(
        self, mock_config: Config, sample_classified_emails: list[ClassifiedEmail]
    ) -> None:
        """Test that HTML includes priority sections."""
        summary = summarize(sample_classified_emails, mock_config)
        html = render_html(summary, mock_config)

        # Check for section titles
        assert "Urgent" in html
        assert "Meetings" in html or "Meeting" in html
        assert "Action" in html


class TestFullRender:
    """Tests for full rendering pipeline."""

    def test_render_digest_returns_tuple(
        self, mock_config: Config, sample_classified_emails: list[ClassifiedEmail]
    ) -> None:
        """Test that render_digest returns plaintext and HTML."""
        summary = summarize(sample_classified_emails, mock_config)
        plaintext, html = render_digest(summary, mock_config)

        assert isinstance(plaintext, str)
        assert isinstance(html, str)
        assert len(plaintext) > 0
        assert len(html) > 0

    def test_render_digest_consistency(
        self, mock_config: Config, sample_classified_emails: list[ClassifiedEmail]
    ) -> None:
        """Test that plaintext and HTML contain similar information."""
        summary = summarize(sample_classified_emails, mock_config)
        plaintext, html = render_digest(summary, mock_config)

        # Check that both contain key information
        for email in sample_classified_emails:
            assert email.email.subject in plaintext
            assert email.email.subject in html
            assert email.email.sender_email in plaintext
            assert email.email.sender_email in html

    def test_render_empty_priority_sections(self, mock_config: Config) -> None:
        """Test rendering with no emails in certain priority sections."""
        # Create sample with only FYI emails
        tz = pytz.timezone("America/New_York")
        email = EmailMessage(
            message_id="msg1",
            thread_id="thread1",
            account_email="test@gmail.com",
            subject="FYI: Update",
            sender="Info <info@company.com>",
            sender_email="info@company.com",
            recipients=["test@gmail.com"],
            date=datetime.now(tz),
            snippet="Just an update",
            body_text="Nothing urgent",
            body_html="",
            labels=["INBOX"],
            has_attachments=False,
            is_reply=False,
            headers={},
            raw_message={},
        )
        classified = ClassifiedEmail(
            email=email,
            priority=Priority.FYI,
            score=3,
            tags=[],
            gist="Just an update",
            reasoning="Low priority",
        )

        summary = summarize([classified], mock_config)
        plaintext, html = render_digest(summary, mock_config)

        # Should still render without errors
        assert "FYI: Update" in plaintext
        assert "FYI: Update" in html
        # Should not have urgent section content
        assert plaintext.count("URGENT") <= 2  # Only in headers, not content

