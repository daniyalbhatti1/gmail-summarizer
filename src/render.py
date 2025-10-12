"""Render email digest in both plaintext and HTML formats."""

import html
import logging
from datetime import datetime
from typing import Any

import pytz

from .classify import ClassifiedEmail, Priority
from .config import Config

logger = logging.getLogger(__name__)


def get_gmail_link(email: ClassifiedEmail) -> str:
    """Generate Gmail web link for a message."""
    # Gmail uses account index (0 for first account)
    # We'll use thread ID which works across all accounts
    return f"https://mail.google.com/mail/u/0/#all/{email.email.thread_id}"


def format_date(dt: datetime) -> str:
    """Format datetime for display."""
    return dt.strftime("%B %d, %Y at %I:%M %p %Z")


def get_time_of_day() -> str:
    """Get time of day label (Morning or Mid-Day)."""
    now = datetime.now()
    if now.hour < 12:
        return "Morning"
    else:
        return "Mid-Day"


def render_plaintext(summary: dict[str, Any], config: Config) -> str:
    """
    Render digest as plaintext.

    Args:
        summary: Summary dictionary from summarize()
        config: Application configuration

    Returns:
        Formatted plaintext email body
    """
    stats = summary["stats"]
    by_priority = stats["by_priority"]
    now = datetime.now(pytz.timezone(config.timezone))
    time_of_day = get_time_of_day()

    lines = []

    # Header
    lines.append("=" * 70)
    lines.append(f"Gmail Digest — {now.strftime('%Y-%m-%d')} — {time_of_day}")
    lines.append("=" * 70)
    lines.append("")

    # At-a-glance summary
    lines.append("AT A GLANCE")
    lines.append("-" * 70)
    lines.append(summary["at_glance"])
    lines.append("")

    # Executive summary (if available)
    if summary.get("executive_summary"):
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 70)
        lines.append(summary["executive_summary"])
        lines.append("")

    # Helper function to render section
    def render_section(title: str, priority: Priority, emoji: str) -> None:
        emails = by_priority.get(priority, [])
        if not emails:
            return

        lines.append(f"{emoji} {title.upper()} ({len(emails)})")
        lines.append("-" * 70)

        for i, classified in enumerate(emails, 1):
            email = classified.email
            lines.append(f"{i}. {email.subject}")
            lines.append(f"   From: {email.sender_email}")
            lines.append(f"   Account: {email.account_email}")
            lines.append(f"   Date: {format_date(email.date)}")
            lines.append(f"   Summary: {classified.gist}")

            if classified.tags:
                lines.append(f"   Tags: {', '.join(classified.tags)}")

            lines.append(f"   View: {get_gmail_link(classified)}")
            lines.append("")

    # Render sections in priority order
    render_section("🔴 Urgent (Time-Sensitive)", Priority.URGENT, "🔴")
    render_section("✅ Action Items", Priority.ACTIONABLE, "✅")
    render_section("📅 Meetings & Events", Priority.MEETING, "📅")
    render_section("💰 Finance & Accounts", Priority.FINANCE, "💰")
    render_section("ℹ️  For Your Information", Priority.FYI, "ℹ️")

    # Footer
    lines.append("=" * 70)
    lines.append("Configuration Tips:")
    lines.append("")
    lines.append("• Edit config.yml to whitelist/blacklist senders or keywords")
    lines.append("• Set USE_LLM=true to enable AI-powered classification")
    lines.append("• Adjust LOOKBACK_HOURS to change how far back we scan")
    lines.append("")
    lines.append("This digest covers the last 48 hours across all configured inboxes.")
    lines.append("=" * 70)

    return "\n".join(lines)


def render_html(summary: dict[str, Any], config: Config) -> str:
    """
    Render digest as HTML.

    Args:
        summary: Summary dictionary from summarize()
        config: Application configuration

    Returns:
        Formatted HTML email body
    """
    stats = summary["stats"]
    by_priority = stats["by_priority"]
    now = datetime.now(pytz.timezone(config.timezone))
    time_of_day = get_time_of_day()

    # Start HTML
    html_parts = [
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        '<title>Gmail Digest</title>',
        '<style>',
        '  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f5f5f5; }',
        '  .container { background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 30px; }',
        '  .header { text-align: center; border-bottom: 3px solid #4285f4; padding-bottom: 20px; margin-bottom: 30px; }',
        '  .header h1 { margin: 0; color: #4285f4; font-size: 28px; }',
        '  .header .date { color: #666; font-size: 16px; margin-top: 5px; }',
        '  .at-glance { background-color: #e8f0fe; border-left: 4px solid #4285f4; padding: 15px 20px; margin-bottom: 30px; border-radius: 4px; }',
        '  .at-glance h2 { margin-top: 0; color: #1967d2; font-size: 18px; }',
        '  .at-glance pre { margin: 0; white-space: pre-wrap; font-family: inherit; }',
        '  .executive-summary { background-color: #fff9e6; border-left: 4px solid #f9ab00; padding: 15px 20px; margin-bottom: 30px; border-radius: 4px; }',
        '  .executive-summary h2 { margin-top: 0; color: #e37400; font-size: 18px; }',
        '  .section { margin-bottom: 40px; }',
        '  .section-header { background-color: #f8f9fa; padding: 10px 15px; border-radius: 4px; margin-bottom: 15px; }',
        '  .section-header h2 { margin: 0; font-size: 20px; display: flex; align-items: center; }',
        '  .section-header .count { margin-left: auto; background-color: #e8eaed; padding: 2px 8px; border-radius: 12px; font-size: 14px; font-weight: normal; }',
        '  .email-item { border-left: 3px solid #dadce0; padding: 15px; margin-bottom: 15px; background-color: #fafafa; border-radius: 4px; transition: background-color 0.2s; }',
        '  .email-item:hover { background-color: #f1f3f4; }',
        '  .email-subject { font-weight: 600; font-size: 16px; color: #1a73e8; margin-bottom: 8px; }',
        '  .email-meta { font-size: 13px; color: #5f6368; margin-bottom: 8px; }',
        '  .email-meta span { margin-right: 15px; }',
        '  .email-summary { font-size: 14px; color: #3c4043; margin-bottom: 8px; font-style: italic; }',
        '  .email-tags { margin-bottom: 8px; }',
        '  .tag { display: inline-block; background-color: #e8f0fe; color: #1967d2; padding: 2px 8px; border-radius: 3px; font-size: 11px; margin-right: 5px; }',
        '  .view-link { display: inline-block; margin-top: 5px; }',
        '  .view-link a { color: #1a73e8; text-decoration: none; font-size: 14px; }',
        '  .view-link a:hover { text-decoration: underline; }',
        '  .footer { border-top: 2px solid #e8eaed; padding-top: 20px; margin-top: 40px; font-size: 13px; color: #5f6368; }',
        '  .footer h3 { font-size: 14px; color: #3c4043; }',
        '  .footer ul { padding-left: 20px; }',
        '  .urgent { border-left-color: #d93025; }',
        '  .actionable { border-left-color: #188038; }',
        '  .meeting { border-left-color: #1967d2; }',
        '  .finance { border-left-color: #f9ab00; }',
        '  .fyi { border-left-color: #9aa0a6; }',
        '</style>',
        '</head>',
        '<body>',
        '<div class="container">',
    ]

    # Header
    html_parts.append('<div class="header">')
    html_parts.append(f'<h1>📬 Gmail Digest</h1>')
    html_parts.append(
        f'<div class="date">{now.strftime("%B %d, %Y")} — {time_of_day}</div>'
    )
    html_parts.append('</div>')

    # At-a-glance summary
    html_parts.append('<div class="at-glance">')
    html_parts.append('<h2>📊 At a Glance</h2>')
    html_parts.append(f'<pre>{html.escape(summary["at_glance"])}</pre>')
    html_parts.append('</div>')

    # Executive summary (if available)
    if summary.get("executive_summary"):
        html_parts.append('<div class="executive-summary">')
        html_parts.append('<h2>📝 Executive Summary</h2>')
        html_parts.append(f'<p>{html.escape(summary["executive_summary"])}</p>')
        html_parts.append('</div>')

    # Helper function to render section
    def render_section(title: str, priority: Priority, emoji: str, css_class: str) -> None:
        emails = by_priority.get(priority, [])
        if not emails:
            return

        html_parts.append('<div class="section">')
        html_parts.append('<div class="section-header">')
        html_parts.append(
            f'<h2>{emoji} {title} <span class="count">{len(emails)}</span></h2>'
        )
        html_parts.append('</div>')

        for classified in emails:
            email = classified.email
            html_parts.append(f'<div class="email-item {css_class}">')
            html_parts.append(
                f'<div class="email-subject">{html.escape(email.subject)}</div>'
            )
            html_parts.append('<div class="email-meta">')
            html_parts.append(f'<span>👤 {html.escape(email.sender_email)}</span>')
            html_parts.append(f'<span>📧 {html.escape(email.account_email)}</span>')
            html_parts.append(f'<span>📅 {html.escape(format_date(email.date))}</span>')
            html_parts.append('</div>')
            html_parts.append(
                f'<div class="email-summary">{html.escape(classified.gist)}</div>'
            )

            if classified.tags:
                html_parts.append('<div class="email-tags">')
                for tag in classified.tags:
                    html_parts.append(f'<span class="tag">{html.escape(tag)}</span>')
                html_parts.append('</div>')

            html_parts.append('<div class="view-link">')
            html_parts.append(
                f'<a href="{get_gmail_link(classified)}" target="_blank">View in Gmail →</a>'
            )
            html_parts.append('</div>')
            html_parts.append('</div>')

        html_parts.append('</div>')

    # Render sections in priority order
    render_section("Urgent (Time-Sensitive)", Priority.URGENT, "🔴", "urgent")
    render_section("Action Items", Priority.ACTIONABLE, "✅", "actionable")
    render_section("Meetings & Events", Priority.MEETING, "📅", "meeting")
    render_section("Finance & Accounts", Priority.FINANCE, "💰", "finance")
    render_section("For Your Information", Priority.FYI, "ℹ️", "fyi")

    # Footer
    html_parts.append('<div class="footer">')
    html_parts.append('<h3>⚙️ Configuration Tips</h3>')
    html_parts.append('<ul>')
    html_parts.append('<li>Edit <code>config.yml</code> to whitelist/blacklist senders or keywords</li>')
    html_parts.append('<li>Set <code>USE_LLM=true</code> to enable AI-powered classification</li>')
    html_parts.append('<li>Adjust <code>LOOKBACK_HOURS</code> to change how far back we scan</li>')
    html_parts.append('</ul>')
    html_parts.append(
        '<p><small>This digest covers the last 48 hours across all configured inboxes.</small></p>'
    )
    html_parts.append('</div>')

    # Close HTML
    html_parts.append('</div>')
    html_parts.append('</body>')
    html_parts.append('</html>')

    return '\n'.join(html_parts)


def render_digest(summary: dict[str, Any], config: Config) -> tuple[str, str]:
    """
    Render digest in both plaintext and HTML formats.

    Args:
        summary: Summary dictionary from summarize()
        config: Application configuration

    Returns:
        Tuple of (plaintext, html)
    """
    plaintext = render_plaintext(summary, config)
    html_content = render_html(summary, config)

    return plaintext, html_content

