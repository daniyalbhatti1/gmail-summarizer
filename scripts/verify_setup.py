#!/usr/bin/env python3
"""
Verify Gmail Digest setup and configuration.

This script checks that all required environment variables are set
and that the configuration is valid.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_env_var(name: str, required: bool = True) -> bool:
    """Check if an environment variable is set."""
    value = os.getenv(name)
    if value:
        print(f"✅ {name}: Set")
        return True
    elif required:
        print(f"❌ {name}: Missing (REQUIRED)")
        return False
    else:
        print(f"⚠️  {name}: Not set (optional)")
        return True


def verify_config() -> bool:
    """Verify configuration can be loaded."""
    try:
        from src.config import get_config

        config = get_config()
        print(f"✅ Configuration loaded successfully")
        print(f"   - Main email: {config.main_email}")
        print(f"   - Accounts: {len(config.accounts)}")
        print(f"   - LLM mode: {'enabled' if config.use_llm else 'disabled'}")
        print(f"   - Timezone: {config.timezone}")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def main() -> None:
    """Main verification function."""
    print("=" * 70)
    print("Gmail Digest Setup Verification")
    print("=" * 70)
    print()

    # Check required environment variables
    print("Checking required environment variables...")
    print("-" * 70)
    all_good = True
    all_good &= check_env_var("MAIN_EMAIL", required=True)
    all_good &= check_env_var("GOOGLE_CLIENT_ID", required=True)
    all_good &= check_env_var("GOOGLE_CLIENT_SECRET", required=True)
    all_good &= check_env_var("GMAIL_ACCOUNTS_JSON", required=True)
    print()

    # Check optional environment variables
    print("Checking optional environment variables...")
    print("-" * 70)
    check_env_var("OPENAI_API_KEY", required=False)
    check_env_var("USE_LLM", required=False)
    check_env_var("TIMEZONE", required=False)
    check_env_var("LOOKBACK_HOURS", required=False)
    print()

    # Try to load configuration
    print("Loading configuration...")
    print("-" * 70)
    if not verify_config():
        all_good = False
    print()

    # Check files exist
    print("Checking required files...")
    print("-" * 70)
    required_files = [
        "config.yml",
        "src/main.py",
        "src/config.py",
        "scripts/generate_tokens.py",
    ]

    base_path = Path(__file__).parent.parent
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✅ {file_path}: Found")
        else:
            print(f"❌ {file_path}: Missing")
            all_good = False
    print()

    # Final status
    print("=" * 70)
    if all_good:
        print("✅ Setup verification PASSED")
        print()
        print("You're all set! Run the digest with:")
        print("  python -m src.main")
        print()
    else:
        print("❌ Setup verification FAILED")
        print()
        print("Please fix the issues above and try again.")
        print("See README.md for setup instructions.")
        print()
    print("=" * 70)

    sys.exit(0 if all_good else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Cancelled by user")
        sys.exit(1)

