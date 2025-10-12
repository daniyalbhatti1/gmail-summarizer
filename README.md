# Gmail Digest 📬

A powerful Python tool that scans **multiple Gmail inboxes**, filters out spam and low-value emails, intelligently classifies important messages, and sends you a beautifully formatted **digest email** twice daily.

## ✨ Features

- 🔐 **Multi-account support** - Monitor multiple Gmail accounts from one place
- 🤖 **Smart classification** - Heuristic-based filtering with optional LLM enhancement
- 📊 **Beautiful summaries** - HTML and plaintext digest emails with priority groupings
- ⏰ **Automated scheduling** - GitHub Actions or Docker with cron (9am & 1pm ET)
- 🎯 **Highly configurable** - Whitelist/blacklist senders, customize scoring, adjust thresholds
- 🔒 **Secure** - OAuth 2.0 flow, no passwords stored, tokens never committed to git
- 🚀 **Easy setup** - Simple token generation script and clear documentation

## 📋 Table of Contents

- [Quick Start](#-quick-start-5-minutes)
- [Setup Options](#-setup-options)
  - [Option A: GitHub Actions (Recommended)](#option-a-github-actions-recommended)
  - [Option B: Local Docker](#option-b-local-docker)
- [Configuration](#-configuration)
- [Customization](#-customization)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Advanced Usage](#-advanced-usage)

## 🚀 Quick Start (5 Minutes)

### Prerequisites

- Python 3.11 or higher
- A Google Cloud account (free tier is fine)
- Gmail account(s) you want to monitor

### 1. Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **Gmail API**:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Gmail API" and click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
   - Choose "Desktop app" as application type
   - Download the credentials
   - Extract `client_id` and `client_secret`

### 2. Clone and Install

```bash
git clone https://github.com/yourusername/gmail-digest.git
cd gmail-digest
pip install -e .
```

### 3. Generate OAuth Tokens

```bash
# Set your OAuth credentials
export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret"

# Run the token generator
python scripts/generate_tokens.py
```

Follow the prompts to authenticate each Gmail account. The script will output a JSON string for `GMAIL_ACCOUNTS_JSON`.

### 4. Choose Your Deployment Method

- **GitHub Actions** (recommended for cloud-based, zero-maintenance operation)
- **Local Docker** (for self-hosted environments)

See [Setup Options](#-setup-options) below for detailed instructions.

## 📦 Setup Options

### Option A: GitHub Actions (Recommended)

Perfect for hands-off, cloud-based operation. The digest will be generated automatically twice daily.

#### Steps:

1. **Fork or push this repo to GitHub**

2. **Configure GitHub Secrets**:
   - Go to your repo → Settings → Secrets and variables → Actions
   - Click "New repository secret" and add:

   ```
   MAIN_EMAIL=your-main-email@gmail.com
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   GMAIL_ACCOUNTS_JSON=[{"email": "account1@gmail.com", "refresh_token": "..."}, ...]
   ```

   Optional secrets:
   ```
   OPENAI_API_KEY=sk-...  (if using LLM mode)
   USE_LLM=true           (default: false)
   TIMEZONE=America/New_York  (default: America/New_York)
   LOOKBACK_HOURS=48      (default: 48)
   ```

3. **Enable GitHub Actions**:
   - Go to "Actions" tab
   - Enable workflows if prompted

4. **Test the workflow**:
   - Go to "Actions" → "Gmail Digest" → "Run workflow"
   - Click "Run workflow" to test manually

That's it! The digest will now run automatically at 9:00 AM and 1:00 PM ET every day.

#### Scheduled Times

The workflow runs at:
- **09:00 AM ET** (Morning digest)
- **01:00 PM ET** (Mid-day digest)

The workflow automatically handles DST (Daylight Saving Time) transitions.

### Option B: Local Docker

Perfect for self-hosted environments or local testing.

#### Steps:

1. **Create environment file**:

```bash
cp .env.example .env
```

2. **Edit `.env` and fill in your values**:

```env
MAIN_EMAIL=your-main-email@gmail.com
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GMAIL_ACCOUNTS_JSON=[{"email": "account1@gmail.com", "refresh_token": "..."}, ...]
```

3. **Build and run**:

```bash
docker-compose up -d
```

4. **Check logs**:

```bash
docker-compose logs -f
```

The digest will run at 9:00 AM and 1:00 PM in your configured timezone.

#### Docker Management

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# View logs
docker-compose logs -f

# Run digest immediately (for testing)
docker-compose exec gmail-digest python -m src.main
```

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MAIN_EMAIL` | ✅ Yes | - | Where to send the digest |
| `GOOGLE_CLIENT_ID` | ✅ Yes | - | OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | ✅ Yes | - | OAuth client secret |
| `GMAIL_ACCOUNTS_JSON` | ✅ Yes | - | JSON array of accounts with refresh tokens |
| `OPENAI_API_KEY` | ❌ No | - | OpenAI API key for LLM mode |
| `USE_LLM` | ❌ No | `false` | Enable LLM-enhanced classification |
| `TIMEZONE` | ❌ No | `America/New_York` | Timezone for scheduling |
| `LOOKBACK_HOURS` | ❌ No | `48` | How many hours back to scan |

### GMAIL_ACCOUNTS_JSON Format

```json
[
  {
    "email": "personal@gmail.com",
    "refresh_token": "1//0abc..."
  },
  {
    "email": "work@gmail.com",
    "refresh_token": "1//0xyz..."
  }
]
```

Generate these tokens using `python scripts/generate_tokens.py`.

## 🎨 Customization

### Filtering Rules (`config.yml`)

Edit `config.yml` to customize classification behavior:

```yaml
# Senders to always mark as important (regex patterns)
whitelist_senders:
  - "boss@company\\.com"
  - ".*@vip-client\\.com"

# Senders to always ignore
blacklist_senders:
  - "noreply@.*"
  - ".*newsletter.*@.*"

# Subject patterns for urgent emails
urgent_subject_patterns:
  - "\\bURGENT\\b"
  - "deadline"
  - "action required"

# Scoring weights (adjust to your preferences)
scoring:
  direct_to_me: 3
  urgent_subject: 5
  whitelist_sender: 10
  blacklist_sender: -100
  # ... see config.yml for full list

# Classification thresholds
thresholds:
  drop: 0        # Score below this gets dropped
  fyi: 2         # Score >= this is FYI
  actionable: 5  # Score >= this is actionable
  urgent: 8      # Score >= this is urgent
```

### Adding/Removing Accounts

1. Run the token generator again:
   ```bash
   python scripts/generate_tokens.py
   ```

2. Update your `GMAIL_ACCOUNTS_JSON` environment variable or secret with the new JSON.

3. For Docker: restart the container
   ```bash
   docker-compose restart
   ```

4. For GitHub Actions: secrets update automatically on next run

### LLM Mode

Enable AI-powered classification and summarization:

1. Get an OpenAI API key from [platform.openai.com](https://platform.openai.com/)

2. Set environment variables:
   ```bash
   export OPENAI_API_KEY="sk-..."
   export USE_LLM="true"
   ```

3. LLM mode:
   - Refines borderline classifications
   - Generates concise summaries of long threads
   - Falls back to heuristics if API fails
   - Uses `gpt-4o-mini` for cost efficiency

**Note**: LLM mode is optional. The heuristic-based classification is already quite effective!

## 🧪 Testing

Run the test suite:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_classify.py -v
```

### Manual Testing

Test the digest generation manually:

```bash
# Set environment variables
export MAIN_EMAIL="your-email@gmail.com"
export GOOGLE_CLIENT_ID="..."
export GOOGLE_CLIENT_SECRET="..."
export GMAIL_ACCOUNTS_JSON='[...]'

# Run once
python -m src.main
```

## 🔧 Troubleshooting

### OAuth Errors

**Problem**: `Invalid credentials` or `Token expired`

**Solution**:
1. Re-run `python scripts/generate_tokens.py`
2. Update your `GMAIL_ACCOUNTS_JSON` with new tokens
3. Make sure scopes haven't changed (requires re-authentication)

### Gmail API Quota Exceeded

**Problem**: `Quota exceeded` errors

**Solution**:
- Gmail API has a default quota of 1 billion units/day (very generous)
- If exceeded, wait 24 hours or request quota increase in Google Cloud Console
- Consider increasing `LOOKBACK_HOURS` to reduce API calls

### No Emails Found

**Problem**: Digest says "No new emails found" but you have emails

**Solution**:
1. Check that `LOOKBACK_HOURS` is sufficient (default: 48)
2. Verify your Gmail search query isn't too restrictive
3. Ensure emails aren't in spam/trash (we filter those out)
4. Check that email accounts are correctly configured

### GitHub Actions Not Running

**Problem**: Workflow doesn't trigger at scheduled times

**Solution**:
1. Verify the workflow file is in `.github/workflows/digest.yml`
2. Ensure Actions are enabled in repo settings
3. Check that all required secrets are set
4. Note: GitHub Actions cron can be delayed by up to 15 minutes during high load

### Docker Container Issues

**Problem**: Container exits immediately

**Solution**:
1. Check logs: `docker-compose logs`
2. Verify `.env` file exists and has all required variables
3. Ensure GMAIL_ACCOUNTS_JSON is properly quoted in `.env`:
   ```
   GMAIL_ACCOUNTS_JSON='[{"email":"...","refresh_token":"..."}]'
   ```

### Email Not Sending

**Problem**: Digest generates but doesn't send

**Solution**:
1. Verify `MAIN_EMAIL` is set correctly
2. Ensure the main email account has send permissions
3. Check that refresh tokens are valid
4. Look for errors in logs

## 🔐 Security Best Practices

1. **Never commit tokens**: The `.gitignore` already excludes `tokens/` and `.env`
2. **Rotate credentials**: Regenerate OAuth tokens periodically
3. **Use minimal scopes**: We only request `gmail.readonly` and `gmail.send`
4. **Monitor access**: Check your Google account's security page regularly
5. **Secure your repo**: If using GitHub Actions, ensure the repo is private or secrets are protected

## 📊 How It Works

1. **Fetch**: Retrieves emails from all configured accounts (last 48 hours by default)
2. **Filter**: Applies Gmail search queries to exclude spam, promotions, etc.
3. **Classify**: Scores each email using heuristics (+ optional LLM)
   - **Urgent**: Time-sensitive, deadlines, high-priority
   - **Actionable**: Requires response or action
   - **Meeting**: Calendar invites, event RSVPs
   - **Finance**: Invoices, payments, transactions
   - **FYI**: Important but not actionable
   - **Low-Value**: Filtered out (newsletters, promotions)
4. **Summarize**: Groups emails by priority, generates statistics
5. **Render**: Creates beautiful HTML and plaintext digest
6. **Send**: Delivers to your main email via Gmail API

## 📈 Roadmap

Potential future enhancements:
- [ ] Slack/Discord notifications
- [ ] Mobile app companion
- [ ] Thread summarization (TL;DR of long chains)
- [ ] Smart reply suggestions
- [ ] Calendar integration (auto-accept/decline)
- [ ] Attachment analysis
- [ ] Sentiment analysis

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest`
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with:
- [Google Gmail API](https://developers.google.com/gmail/api)
- [OpenAI API](https://platform.openai.com/) (optional)
- Python 3.11+

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/gmail-digest/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/gmail-digest/discussions)

---

Made with ❤️ for inbox zero enthusiasts

