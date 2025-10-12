#!/usr/bin/env python3
"""
Generate OAuth refresh tokens for Gmail accounts.

This script guides you through the OAuth flow for each Gmail account
and outputs refresh tokens that you can use in GMAIL_ACCOUNTS_JSON.
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail API scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


def get_credentials_from_env() -> tuple[str, str]:
    """Get OAuth client credentials from environment or prompt."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("=" * 70)
        print("OAuth Credentials Required")
        print("=" * 70)
        print()
        print("To get these credentials:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project (or select existing)")
        print("3. Enable Gmail API")
        print("4. Go to 'Credentials' → 'Create Credentials' → 'OAuth 2.0 Client ID'")
        print("5. Choose 'Desktop app' as application type")
        print("6. Copy the client_id and client_secret")
        print()
        print("-" * 70)
        print()
        
        if not client_id:
            client_id = input("Enter your GOOGLE_CLIENT_ID: ").strip()
            if not client_id:
                print("ERROR: Client ID is required")
                sys.exit(1)
        
        if not client_secret:
            client_secret = input("Enter your GOOGLE_CLIENT_SECRET: ").strip()
            if not client_secret:
                print("ERROR: Client Secret is required")
                sys.exit(1)
        
        print()

    return client_id, client_secret


def create_oauth_config(client_id: str, client_secret: str) -> dict:
    """Create OAuth configuration for InstalledAppFlow."""
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost:8080/", "urn:ietf:wg:oauth:2.0:oob"],
        }
    }


def generate_token(email: str, client_id: str, client_secret: str) -> str | None:
    """
    Generate refresh token for a Gmail account.

    Args:
        email: Email address hint
        client_id: OAuth client ID
        client_secret: OAuth client secret

    Returns:
        Refresh token or None if failed
    """
    try:
        config = create_oauth_config(client_id, client_secret)

        # Create flow
        flow = InstalledAppFlow.from_client_config(
            config, SCOPES, redirect_uri="http://localhost:8080/"
        )

        print()
        print("-" * 70)
        print(f"Generating token for: {email}")
        print("-" * 70)
        print()
        print("Your browser will open shortly...")
        print("Please sign in with the Gmail account you want to add.")
        print()

        # Run local server to receive OAuth callback
        creds = flow.run_local_server(
            port=8080,
            prompt="consent",
            success_message="Authentication successful! You can close this window.",
        )

        if creds and creds.refresh_token:
            print()
            print("✅ Successfully authenticated!")
            print()
            return creds.refresh_token
        else:
            print()
            print("❌ Failed to get refresh token")
            print()
            return None

    except Exception as e:
        print()
        print(f"❌ Error during authentication: {e}")
        print()
        return None


def main() -> None:
    """Main function."""
    print()
    print("=" * 70)
    print("Gmail Digest - OAuth Token Generator")
    print("=" * 70)
    print()
    print("This script will help you generate refresh tokens for your Gmail accounts.")
    print()

    # Get OAuth credentials
    client_id, client_secret = get_credentials_from_env()

    print("OAuth credentials loaded successfully!")
    print()

    # Ask how many accounts to configure
    while True:
        try:
            num_accounts = int(input("How many Gmail accounts do you want to configure? "))
            if num_accounts > 0:
                break
            print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")

    accounts = []

    for i in range(num_accounts):
        print()
        print("=" * 70)
        print(f"Account {i + 1} of {num_accounts}")
        print("=" * 70)

        email = input("Enter the Gmail address: ").strip()

        if not email or "@" not in email:
            print("Invalid email address. Skipping...")
            continue

        refresh_token = generate_token(email, client_id, client_secret)

        if refresh_token:
            accounts.append({"email": email, "refresh_token": refresh_token})
        else:
            print(f"Failed to generate token for {email}. Skipping...")

    if not accounts:
        print()
        print("❌ No accounts were configured successfully.")
        print()
        sys.exit(1)

    # Display results
    print()
    print("=" * 70)
    print("✅ Token Generation Complete!")
    print("=" * 70)
    print()
    print(f"Successfully configured {len(accounts)} account(s):")
    for acc in accounts:
        print(f"  • {acc['email']}")
    print()

    # Generate JSON
    accounts_json = json.dumps(accounts)

    print("-" * 70)
    print("GMAIL_ACCOUNTS_JSON value:")
    print("-" * 70)
    print()
    print(accounts_json)
    print()
    print("-" * 70)
    print()

    # Save to local file (optional)
    save_local = input("Save tokens to local file tokens/credentials.json? (y/N): ").strip().lower()

    if save_local == "y":
        tokens_dir = Path(__file__).parent.parent / "tokens"
        tokens_dir.mkdir(exist_ok=True)

        tokens_file = tokens_dir / "credentials.json"
        with open(tokens_file, "w") as f:
            json.dump(accounts, f, indent=2)

        print()
        print(f"✅ Tokens saved to: {tokens_file}")
        print()
        print("⚠️  IMPORTANT: This file contains sensitive credentials!")
        print("   Never commit it to git. It's already in .gitignore.")
        print()

    # Instructions
    print("=" * 70)
    print("Next Steps:")
    print("=" * 70)
    print()
    print("For GitHub Actions:")
    print("  1. Go to your repo → Settings → Secrets and variables → Actions")
    print("  2. Create a new secret: GMAIL_ACCOUNTS_JSON")
    print("  3. Paste the JSON value shown above")
    print()
    print("For local Docker/.env:")
    print("  1. Copy .env.example to .env")
    print("  2. Add: GMAIL_ACCOUNTS_JSON='<paste JSON here>'")
    print()
    print("Don't forget to also set:")
    print("  - MAIN_EMAIL (where you want to receive the digest)")
    print("  - GOOGLE_CLIENT_ID")
    print("  - GOOGLE_CLIENT_SECRET")
    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print()
        print("❌ Cancelled by user")
        print()
        sys.exit(1)

