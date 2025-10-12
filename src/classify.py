"""Email classification using heuristics and optional LLM enhancement."""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .config import Config
from .fetch import EmailMessage

logger = logging.getLogger(__name__)


class Priority(Enum):
    """Email priority levels."""

    URGENT = "urgent"
    ACTIONABLE = "actionable"
    MEETING = "meeting"
    FINANCE = "finance"
    FYI = "fyi"
    LOW_VALUE = "low_value"


@dataclass
class ClassifiedEmail:
    """Email with classification results."""

    email: EmailMessage
    priority: Priority
    score: int
    tags: list[str]
    gist: str  # One-line summary
    reasoning: str  # Why this classification was chosen


def calculate_heuristic_score(email: EmailMessage, config: Config) -> tuple[int, list[str]]:
    """
    Calculate importance score using heuristics.

    Returns:
        Tuple of (score, tags) where tags are the detected signals
    """
    score = 0
    tags: list[str] = []

    # Check if sender is whitelisted
    if config.matches_pattern(email.sender_email, config.whitelist_senders):
        score += config.scoring.get("whitelist_sender", 10)
        tags.append("whitelisted-sender")

    # Check if sender is blacklisted
    if config.matches_pattern(email.sender_email, config.blacklist_senders):
        score += config.scoring.get("blacklist_sender", -100)
        tags.append("blacklisted-sender")
        return score, tags  # Early exit for blacklisted

    # Check for promotional categories
    if any(label in email.labels for label in config.ignore_labels):
        score += config.scoring.get("promotional_category", -10)
        tags.append("promotional")

    # Check if directly addressed to the user
    if any(email.account_email.lower() in recipient.lower() for recipient in email.recipients):
        score += config.scoring.get("direct_to_me", 3)
        tags.append("direct-to-me")

    # Check if it's a reply chain
    if email.is_reply:
        score += config.scoring.get("reply_chain", 2)
        tags.append("reply-chain")

    # Check for Gmail IMPORTANT label
    if "IMPORTANT" in email.labels:
        score += config.scoring.get("important_label", 2)
        tags.append("important-label")

    # Check urgent subject patterns
    if config.matches_pattern(email.subject, config.urgent_subject_patterns):
        score += config.scoring.get("urgent_subject", 5)
        tags.append("urgent-subject")

    # Check ignore subject patterns
    if config.matches_pattern(email.subject, config.ignore_subject_patterns):
        score += config.scoring.get("promotional_category", -10)
        tags.append("ignorable-subject")

    # Check important body keywords
    body_text = (email.body_text or email.snippet).lower()
    if config.matches_pattern(body_text, config.important_body_keywords):
        score += config.scoring.get("urgent_body", 3)
        tags.append("urgent-body")

    # Check for attachments
    if email.has_attachments:
        score += config.scoring.get("has_attachment", 1)
        tags.append("has-attachment")

    # Check for calendar invites
    if any(
        pattern in email.subject.lower() or pattern in body_text
        for pattern in ["calendar", "invite", "meeting", "event", ".ics"]
    ):
        score += config.scoring.get("calendar_invite", 4)
        tags.append("calendar-invite")

    # Check for unsubscribe links (promotional indicator)
    if "unsubscribe" in body_text:
        score += config.scoring.get("has_unsubscribe_link", -2)
        tags.append("has-unsubscribe")

    # Check for bulk email headers
    if any(
        header in email.headers
        for header in ["List-Unsubscribe", "List-Id", "Precedence"]
    ):
        score += config.scoring.get("bulk_headers", -3)
        tags.append("bulk-email")

    # Check for financial keywords
    financial_keywords = [
        "invoice",
        "payment",
        "receipt",
        "transaction",
        "bill",
        "charge",
        "refund",
        "statement",
    ]
    if any(kw in email.subject.lower() or kw in body_text for kw in financial_keywords):
        tags.append("finance")

    # Check for deadline/time-sensitive keywords
    deadline_patterns = [
        r"due.*\d{1,2}/\d{1,2}",
        r"deadline.*\d{1,2}/\d{1,2}",
        r"by.*\d{1,2}:\d{2}",
        r"expires.*\d{1,2}/\d{1,2}",
        r"before.*\d{1,2}/\d{1,2}",
    ]
    if any(re.search(pattern, body_text, re.IGNORECASE) for pattern in deadline_patterns):
        score += 3
        tags.append("has-deadline")

    return score, tags


def classify_by_score(score: int, tags: list[str], config: Config) -> Priority:
    """
    Determine priority bucket based on score and tags.

    Priority:
        1. Urgent: High score or deadline-related
        2. Meeting: Calendar/event related
        3. Actionable: Moderate score, requires action
        4. Finance: Financial transactions
        5. FYI: Low-moderate score, informational
        6. Low Value: Below threshold
    """
    thresholds = config.thresholds

    # Special case: calendar invites
    if "calendar-invite" in tags:
        return Priority.MEETING

    # Special case: deadlines or very high scores
    if "has-deadline" in tags or score >= thresholds.get("urgent", 8):
        return Priority.URGENT

    # Financial emails
    if "finance" in tags and score >= thresholds.get("actionable", 5):
        return Priority.FINANCE

    # Actionable items
    if score >= thresholds.get("actionable", 5):
        return Priority.ACTIONABLE

    # FYI items
    if score >= thresholds.get("fyi", 2):
        return Priority.FYI

    # Low value or should be dropped
    return Priority.LOW_VALUE


def generate_gist(email: EmailMessage) -> str:
    """Generate a one-line gist from email content."""
    # Use snippet or first line of body
    text = email.snippet or email.body_text
    if not text:
        return "No preview available"

    # Clean up and truncate
    text = text.strip().replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text)

    # Truncate to ~100 characters
    if len(text) > 100:
        text = text[:97] + "..."

    return text


def classify_email_heuristic(email: EmailMessage, config: Config) -> ClassifiedEmail:
    """
    Classify email using heuristic rules only.

    Args:
        email: Email to classify
        config: Application configuration

    Returns:
        ClassifiedEmail with classification results
    """
    score, tags = calculate_heuristic_score(email, config)
    priority = classify_by_score(score, tags, config)
    gist = generate_gist(email)

    reasoning = f"Score: {score}, Tags: {', '.join(tags) if tags else 'none'}"

    return ClassifiedEmail(
        email=email,
        priority=priority,
        score=score,
        tags=tags,
        gist=gist,
        reasoning=reasoning,
    )


def classify_email_llm(
    email: EmailMessage, heuristic_result: ClassifiedEmail, config: Config
) -> ClassifiedEmail:
    """
    Enhance classification using LLM (optional).

    Falls back to heuristic result if LLM fails.

    Args:
        email: Email to classify
        heuristic_result: Result from heuristic classification
        config: Application configuration

    Returns:
        Enhanced ClassifiedEmail
    """
    if not config.use_llm or not config.openai_api_key:
        return heuristic_result

    try:
        import openai

        client = openai.OpenAI(api_key=config.openai_api_key)

        prompt = f"""Classify this email and provide a brief summary.

Subject: {email.subject}
From: {email.sender}
Date: {email.date.strftime('%Y-%m-%d %H:%M')}
Preview: {email.snippet[:200]}

Current heuristic classification: {heuristic_result.priority.value}
Score: {heuristic_result.score}
Tags: {', '.join(heuristic_result.tags)}

Please respond with JSON:
{{
    "priority": "urgent|actionable|meeting|finance|fyi|low_value",
    "gist": "one-line summary (max 100 chars)",
    "reasoning": "brief explanation"
}}

Focus on:
- Is this time-sensitive or has a deadline?
- Does it require action from the recipient?
- Is it a meeting/calendar invite?
- Is it promotional/low-value?
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
            response_format={"type": "json_object"},
        )

        result = response.choices[0].message.content
        if not result:
            return heuristic_result

        import json

        llm_result = json.loads(result)

        # Map LLM priority to our Priority enum
        priority_map = {
            "urgent": Priority.URGENT,
            "actionable": Priority.ACTIONABLE,
            "meeting": Priority.MEETING,
            "finance": Priority.FINANCE,
            "fyi": Priority.FYI,
            "low_value": Priority.LOW_VALUE,
        }

        priority = priority_map.get(llm_result.get("priority", "fyi").lower(), Priority.FYI)
        gist = llm_result.get("gist", heuristic_result.gist)[:100]
        reasoning = f"LLM: {llm_result.get('reasoning', 'No reasoning provided')}"

        return ClassifiedEmail(
            email=email,
            priority=priority,
            score=heuristic_result.score,
            tags=heuristic_result.tags + ["llm-enhanced"],
            gist=gist,
            reasoning=reasoning,
        )

    except Exception as e:
        logger.warning(f"LLM classification failed, falling back to heuristics: {e}")
        return heuristic_result


def classify_emails(emails: list[EmailMessage], config: Config) -> list[ClassifiedEmail]:
    """
    Classify a batch of emails.

    Args:
        emails: List of emails to classify
        config: Application configuration

    Returns:
        List of classified emails, filtered to remove low-value items
    """
    classified: list[ClassifiedEmail] = []

    for email in emails:
        # Get heuristic classification
        heuristic_result = classify_email_heuristic(email, config)

        # Optionally enhance with LLM
        if config.use_llm and heuristic_result.priority != Priority.LOW_VALUE:
            result = classify_email_llm(email, heuristic_result, config)
        else:
            result = heuristic_result

        # Filter out low-value emails
        if result.priority != Priority.LOW_VALUE:
            classified.append(result)

    logger.info(
        f"Classified {len(classified)} emails (filtered {len(emails) - len(classified)} low-value)"
    )

    return classified

