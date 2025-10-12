"""Generate summary statistics and aggregate information."""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

from .classify import ClassifiedEmail, Priority
from .config import Config

logger = logging.getLogger(__name__)


def generate_summary_stats(classified_emails: list[ClassifiedEmail]) -> dict[str, Any]:
    """
    Generate summary statistics from classified emails.

    Returns:
        Dictionary with counts, top items, and other statistics
    """
    # Count by priority
    priority_counts: dict[Priority, int] = defaultdict(int)
    for email in classified_emails:
        priority_counts[email.priority] += 1

    # Group by priority
    by_priority: dict[Priority, list[ClassifiedEmail]] = defaultdict(list)
    for email in classified_emails:
        by_priority[email.priority].append(email)

    # Sort each priority group by score (descending)
    for priority in by_priority:
        by_priority[priority].sort(key=lambda e: e.score, reverse=True)

    # Extract top 3 most critical items
    critical_items: list[ClassifiedEmail] = []

    # Priority order for critical items
    for priority in [Priority.URGENT, Priority.ACTIONABLE, Priority.MEETING]:
        items = by_priority.get(priority, [])
        for item in items:
            if len(critical_items) < 3:
                critical_items.append(item)

    return {
        "total_count": len(classified_emails),
        "priority_counts": {p.value: count for p, count in priority_counts.items()},
        "by_priority": by_priority,
        "critical_items": critical_items,
    }




def generate_at_glance_summary(stats: dict[str, Any]) -> str:
    """
    Generate an at-a-glance text summary.

    Returns:
        Plaintext summary with counts and critical items
    """
    lines = []

    # Overall counts
    counts = stats["priority_counts"]
    lines.append(f"📊 Total: {stats['total_count']} emails")

    if counts.get("urgent", 0) > 0:
        lines.append(f"🔴 Urgent: {counts['urgent']}")
    if counts.get("actionable", 0) > 0:
        lines.append(f"✅ Action Items: {counts['actionable']}")
    if counts.get("meeting", 0) > 0:
        lines.append(f"📅 Meetings: {counts['meeting']}")
    if counts.get("finance", 0) > 0:
        lines.append(f"💰 Finance: {counts['finance']}")
    if counts.get("fyi", 0) > 0:
        lines.append(f"ℹ️  FYI: {counts['fyi']}")

    # Critical items
    critical = stats["critical_items"]
    if critical:
        lines.append("\n📌 Top Priority:")
        for item in critical[:3]:
            # Extract deadline if present
            deadline_info = ""
            if "has-deadline" in item.tags:
                deadline_info = " [TIME-SENSITIVE]"

            lines.append(
                f"  • {item.email.subject[:60]}{deadline_info}\n"
                f"    From: {item.email.sender_email}"
            )

    return "\n".join(lines)


def summarize(classified_emails: list[ClassifiedEmail], config: Config) -> dict[str, Any]:
    """
    Generate comprehensive summary of classified emails.

    Args:
        classified_emails: List of classified emails
        config: Application configuration

    Returns:
        Dictionary containing:
            - stats: Statistics and groupings
            - at_glance: Quick text summary
    """
    stats = generate_summary_stats(classified_emails)
    at_glance = generate_at_glance_summary(stats)

    return {
        "stats": stats,
        "at_glance": at_glance,
        "executive_summary": None,
        "timestamp": datetime.now(),
    }

