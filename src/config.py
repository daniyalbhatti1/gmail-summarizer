"""Configuration management for Gmail Digest."""

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AccountConfig:
    """Configuration for a single Gmail account."""

    email: str
    refresh_token: str


@dataclass
class Config:
    """Application configuration."""

    main_email: str
    accounts: list[AccountConfig]
    google_client_id: str
    google_client_secret: str
    openai_api_key: str | None
    use_llm: bool
    timezone: str
    lookback_hours: int
    whitelist_senders: list[str]
    blacklist_senders: list[str]
    urgent_subject_patterns: list[str]
    ignore_subject_patterns: list[str]
    important_body_keywords: list[str]
    ignore_labels: list[str]
    scoring: dict[str, int]
    thresholds: dict[str, int]

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables and config.yml."""
        # Load from environment
        main_email = os.getenv("MAIN_EMAIL", "")
        if not main_email:
            raise ValueError("MAIN_EMAIL environment variable is required")

        google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        if not google_client_id:
            raise ValueError("GOOGLE_CLIENT_ID environment variable is required")

        google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
        if not google_client_secret:
            raise ValueError("GOOGLE_CLIENT_SECRET environment variable is required")

        # Parse accounts JSON
        accounts_json = os.getenv("GMAIL_ACCOUNTS_JSON", "[]")
        try:
            accounts_data = json.loads(accounts_json)
            accounts = [
                AccountConfig(email=acc["email"], refresh_token=acc["refresh_token"])
                for acc in accounts_data
            ]
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Invalid GMAIL_ACCOUNTS_JSON format: {e}")

        if not accounts:
            raise ValueError("At least one Gmail account must be configured")

        openai_api_key = os.getenv("OPENAI_API_KEY") or None
        use_llm_env = os.getenv("USE_LLM", "false").strip()
        use_llm = use_llm_env.lower() == "true" if use_llm_env else False
        timezone = os.getenv("TIMEZONE", "America/New_York").strip() or "America/New_York"
        lookback_hours_env = os.getenv("LOOKBACK_HOURS", "48").strip()
        lookback_hours = int(lookback_hours_env) if lookback_hours_env else 48

        # Load user-editable config from YAML
        config_path = Path(__file__).parent.parent / "config.yml"
        if config_path.exists():
            with open(config_path, "r") as f:
                yaml_config = yaml.safe_load(f) or {}
        else:
            yaml_config = {}

        return cls(
            main_email=main_email,
            accounts=accounts,
            google_client_id=google_client_id,
            google_client_secret=google_client_secret,
            openai_api_key=openai_api_key,
            use_llm=use_llm,
            timezone=timezone,
            lookback_hours=lookback_hours,
            whitelist_senders=yaml_config.get("whitelist_senders", []),
            blacklist_senders=yaml_config.get("blacklist_senders", []),
            urgent_subject_patterns=yaml_config.get("urgent_subject_patterns", []),
            ignore_subject_patterns=yaml_config.get("ignore_subject_patterns", []),
            important_body_keywords=yaml_config.get("important_body_keywords", []),
            ignore_labels=yaml_config.get("ignore_labels", []),
            scoring=yaml_config.get("scoring", {}),
            thresholds=yaml_config.get("thresholds", {}),
        )

    def matches_pattern(self, text: str, patterns: list[str]) -> bool:
        """Check if text matches any of the given regex patterns."""
        for pattern in patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            except re.error:
                continue
        return False


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config

