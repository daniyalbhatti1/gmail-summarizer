"""Tests for email classification."""

import json
from datetime import datetime
from pathlib import Path

import pytest
import pytz

from src.classify import (
    Priority,
    calculate_heuristic_score,
    classify_by_score,
    classify_email_heuristic,
    generate_gist,
)
from src.config import Config
from src.fetch import EmailMessage


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
        whitelist_senders=["boss@company\\.com"],
        blacklist_senders=["noreply@.*", "marketing@.*"],
        urgent_subject_patterns=["URGENT", "deadline", "action required"],
        ignore_subject_patterns=["% off", "sale ends", "newsletter"],
        important_body_keywords=["due date", "deadline", "needs your approval"],
        ignore_labels=["CATEGORY_PROMOTIONS", "SPAM"],
        scoring={
            "direct_to_me": 3,
            "from_known_contact": 2,
            "reply_chain": 2,
            "important_label": 2,
            "urgent_subject": 5,
            "urgent_body": 3,
            "has_attachment": 1,
            "calendar_invite": 4,
            "whitelist_sender": 10,
            "blacklist_sender": -100,
            "promotional_category": -10,
            "has_unsubscribe_link": -2,
            "bulk_headers": -3,
        },
        thresholds={"drop": 0, "fyi": 2, "actionable": 5, "urgent": 8},
    )


@pytest.fixture
def sample_messages() -> list[dict]:
    """Load sample messages from fixtures."""
    fixtures_path = Path(__file__).parent / "fixtures" / "sample_messages.json"
    with open(fixtures_path, "r") as f:
        return json.load(f)


def create_email_from_dict(data: dict) -> EmailMessage:
    """Create EmailMessage from dictionary."""
    tz = pytz.timezone("America/New_York")
    return EmailMessage(
        message_id=data["message_id"],
        thread_id=data["thread_id"],
        account_email=data["account_email"],
        subject=data["subject"],
        sender=data["sender"],
        sender_email=data["sender_email"],
        recipients=data["recipients"],
        date=datetime.now(tz),
        snippet=data["snippet"],
        body_text=data["body_text"],
        body_html="",
        labels=data["labels"],
        has_attachments=data["has_attachments"],
        is_reply=data["is_reply"],
        headers={},
        raw_message={},
    )


class TestHeuristicScoring:
    """Tests for heuristic scoring."""

    def test_urgent_deadline_email(self, mock_config: Config, sample_messages: list[dict]) -> None:
        """Test that urgent deadline emails get high scores."""
        email = create_email_from_dict(sample_messages[0])  # URGENT deadline email
        score, tags = calculate_heuristic_score(email, mock_config)

        assert score > 0, "Urgent email should have positive score"
        assert "urgent-subject" in tags, "Should detect urgent subject"
        assert "important-label" in tags, "Should detect important label"

    def test_promotional_email_low_score(
        self, mock_config: Config, sample_messages: list[dict]
    ) -> None:
        """Test that promotional emails get low/negative scores."""
        email = create_email_from_dict(sample_messages[2])  # 50% OFF promotional
        score, tags = calculate_heuristic_score(email, mock_config)

        assert score < 0, "Promotional email should have negative score"
        assert "promotional" in tags, "Should detect promotional category"
        assert "has-unsubscribe" in tags, "Should detect unsubscribe link"

    def test_calendar_invite(self, mock_config: Config, sample_messages: list[dict]) -> None:
        """Test that calendar invites are detected."""
        email = create_email_from_dict(sample_messages[1])  # Meeting invite
        score, tags = calculate_heuristic_score(email, mock_config)

        assert "calendar-invite" in tags, "Should detect calendar invite"
        assert score > 0, "Calendar invite should have positive score"

    def test_finance_email(self, mock_config: Config, sample_messages: list[dict]) -> None:
        """Test that financial emails are detected."""
        email = create_email_from_dict(sample_messages[3])  # Invoice payment due
        score, tags = calculate_heuristic_score(email, mock_config)

        assert "finance" in tags, "Should detect finance-related email"
        assert "has-attachment" in tags, "Should detect attachment"
        assert score > 0, "Invoice should have positive score"

    def test_blacklisted_sender(self, mock_config: Config, sample_messages: list[dict]) -> None:
        """Test that blacklisted senders get very negative scores."""
        email = create_email_from_dict(sample_messages[2])  # From marketing@
        score, tags = calculate_heuristic_score(email, mock_config)

        assert score < -50, "Blacklisted sender should have very negative score"
        assert "blacklisted-sender" in tags, "Should detect blacklisted sender"

    def test_whitelisted_sender(self, mock_config: Config, sample_messages: list[dict]) -> None:
        """Test that whitelisted senders get high scores."""
        email = create_email_from_dict(sample_messages[0])  # From boss@
        score, tags = calculate_heuristic_score(email, mock_config)

        assert score > 8, "Whitelisted sender should have high score"
        assert "whitelisted-sender" in tags, "Should detect whitelisted sender"

    def test_reply_chain(self, mock_config: Config, sample_messages: list[dict]) -> None:
        """Test that reply chains get appropriate scores."""
        email = create_email_from_dict(sample_messages[5])  # Re: Action Required
        score, tags = calculate_heuristic_score(email, mock_config)

        assert "reply-chain" in tags, "Should detect reply chain"
        assert score > 0, "Reply chain should have positive contribution"


class TestClassification:
    """Tests for email classification."""

    def test_classify_urgent(self, mock_config: Config, sample_messages: list[dict]) -> None:
        """Test urgent classification."""
        email = create_email_from_dict(sample_messages[0])  # URGENT deadline
        classified = classify_email_heuristic(email, mock_config)

        assert classified.priority == Priority.URGENT, "Should classify as urgent"
        assert classified.score > 8, "Should have high score"

    def test_classify_meeting(self, mock_config: Config, sample_messages: list[dict]) -> None:
        """Test meeting classification."""
        email = create_email_from_dict(sample_messages[1])  # Meeting invite
        classified = classify_email_heuristic(email, mock_config)

        assert classified.priority == Priority.MEETING, "Should classify as meeting"
        assert "calendar-invite" in classified.tags

    def test_classify_low_value(self, mock_config: Config, sample_messages: list[dict]) -> None:
        """Test low-value classification."""
        email = create_email_from_dict(sample_messages[2])  # Promotional
        classified = classify_email_heuristic(email, mock_config)

        assert classified.priority == Priority.LOW_VALUE, "Should classify as low-value"
        assert classified.score < 0

    def test_classify_finance(self, mock_config: Config, sample_messages: list[dict]) -> None:
        """Test finance classification."""
        email = create_email_from_dict(sample_messages[3])  # Invoice
        classified = classify_email_heuristic(email, mock_config)

        assert classified.priority in [
            Priority.FINANCE,
            Priority.ACTIONABLE,
        ], "Should classify as finance or actionable"
        assert "finance" in classified.tags

    def test_classify_actionable(self, mock_config: Config, sample_messages: list[dict]) -> None:
        """Test actionable classification."""
        email = create_email_from_dict(sample_messages[5])  # Action Required
        classified = classify_email_heuristic(email, mock_config)

        assert classified.priority in [
            Priority.ACTIONABLE,
            Priority.URGENT,
        ], "Should classify as actionable or urgent"


class TestGistGeneration:
    """Tests for gist generation."""

    def test_generate_gist_from_snippet(self) -> None:
        """Test gist generation from snippet."""
        email = EmailMessage(
            message_id="test",
            thread_id="test",
            account_email="test@gmail.com",
            subject="Test",
            sender="Test",
            sender_email="test@example.com",
            recipients=["test@gmail.com"],
            date=datetime.now(pytz.UTC),
            snippet="This is a test snippet that should be used for the gist",
            body_text="",
            body_html="",
            labels=[],
            has_attachments=False,
            is_reply=False,
            headers={},
            raw_message={},
        )

        gist = generate_gist(email)
        assert len(gist) <= 103, "Gist should be truncated"
        assert "test snippet" in gist.lower()

    def test_generate_gist_truncation(self) -> None:
        """Test that long gists are truncated."""
        long_text = "A" * 200
        email = EmailMessage(
            message_id="test",
            thread_id="test",
            account_email="test@gmail.com",
            subject="Test",
            sender="Test",
            sender_email="test@example.com",
            recipients=["test@gmail.com"],
            date=datetime.now(pytz.UTC),
            snippet=long_text,
            body_text="",
            body_html="",
            labels=[],
            has_attachments=False,
            is_reply=False,
            headers={},
            raw_message={},
        )

        gist = generate_gist(email)
        assert len(gist) <= 103, "Gist should be truncated to ~100 chars"
        assert gist.endswith("..."), "Truncated gist should end with ..."


class TestClassifyByScore:
    """Tests for score-based classification."""

    def test_urgent_threshold(self, mock_config: Config) -> None:
        """Test urgent threshold."""
        priority = classify_by_score(10, ["has-deadline"], mock_config)
        assert priority == Priority.URGENT

    def test_calendar_override(self, mock_config: Config) -> None:
        """Test that calendar invite overrides score."""
        priority = classify_by_score(3, ["calendar-invite"], mock_config)
        assert priority == Priority.MEETING

    def test_finance_classification(self, mock_config: Config) -> None:
        """Test finance classification."""
        priority = classify_by_score(6, ["finance"], mock_config)
        assert priority == Priority.FINANCE

    def test_actionable_threshold(self, mock_config: Config) -> None:
        """Test actionable threshold."""
        priority = classify_by_score(6, [], mock_config)
        assert priority == Priority.ACTIONABLE

    def test_fyi_threshold(self, mock_config: Config) -> None:
        """Test FYI threshold."""
        priority = classify_by_score(3, [], mock_config)
        assert priority == Priority.FYI

    def test_low_value_threshold(self, mock_config: Config) -> None:
        """Test low-value threshold."""
        priority = classify_by_score(-5, [], mock_config)
        assert priority == Priority.LOW_VALUE

