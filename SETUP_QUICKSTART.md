# Gmail Digest - Quick Setup Guide

This is a condensed setup guide to get you running in under 10 minutes.

## ⚡ Super Quick Setup (GitHub Actions)

### Step 1: Google OAuth (5 minutes)

1. Go to https://console.cloud.google.com/
2. Create project → Enable Gmail API
3. Credentials → Create OAuth 2.0 Client ID → Desktop app
4. Copy the `client_id` and `client_secret`

### Step 2: Generate Tokens (2 minutes)

```bash
cd gmail-digest
pip install -e .

export GOOGLE_CLIENT_ID="your-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-secret"

python scripts/generate_tokens.py
```

Follow the browser prompts for each Gmail account. Copy the output JSON.

### Step 3: Configure GitHub (2 minutes)

1. Push this repo to your GitHub account
2. Go to Settings → Secrets → Actions
3. Add these secrets:

```
MAIN_EMAIL=you@gmail.com
GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret
GMAIL_ACCOUNTS_JSON=[{"email":"...","refresh_token":"..."}]
```

### Step 4: Enable & Test (1 minute)

1. Go to Actions tab → Enable workflows
2. Click "Gmail Digest" → "Run workflow" → Test it!

**Done!** You'll now get digest emails at 9am and 1pm ET automatically.

---

## 🐳 Docker Setup (Alternative)

### If you prefer self-hosted:

```bash
cd gmail-digest

# Generate tokens (same as above)
python scripts/generate_tokens.py

# Create .env file
cat > .env << EOF
MAIN_EMAIL=you@gmail.com
GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret
GMAIL_ACCOUNTS_JSON='[{"email":"...","refresh_token":"..."}]'
EOF

# Start!
docker-compose up -d

# Check logs
docker-compose logs -f
```

---

## 🎯 Verification

Test that everything works:

```bash
# Verify setup
python scripts/verify_setup.py

# Run manually (sends digest immediately)
python -m src.main
```

Check your `MAIN_EMAIL` inbox for the digest!

---

## 🔧 Customization

Edit `config.yml` to customize:
- Whitelist/blacklist senders
- Urgent keywords
- Scoring weights
- Classification thresholds

Changes apply immediately (no restart needed for manual runs, restart container for Docker).

---

## 🆘 Troubleshooting

**"Invalid credentials"**
→ Re-run `python scripts/generate_tokens.py`

**"No emails found"**
→ Increase `LOOKBACK_HOURS=72` (default: 48)

**GitHub Actions not running**
→ Check that secrets are set correctly

**Docker container exits**
→ Check logs: `docker-compose logs`
→ Verify `.env` file format

---

## 📚 More Info

- **Full documentation**: See `README.md`
- **Configuration guide**: See `config.yml`
- **Contributing**: See `CONTRIBUTING.md`
- **Project overview**: See `PROJECT_SUMMARY.md`

---

## 🚀 Next Steps

1. ✅ Set up and test (you're here!)
2. 📝 Customize filters in `config.yml`
3. 🤖 Optionally enable LLM mode (set `OPENAI_API_KEY` + `USE_LLM=true`)
4. 📊 Monitor your first few digests and adjust settings
5. ⭐ Star the repo if you find it useful!

---

**Need help?** Open an issue on GitHub!

