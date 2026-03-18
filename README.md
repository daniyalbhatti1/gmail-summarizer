# Gmail Digest

A Python script that fetches your unread Gmail messages from the past day, summarizes them using OpenAI, and emails you a categorized digest.

## How It Works

1. Connects to your Gmail via the Gmail API
2. Fetches unread emails from the last 24 hours (excluding promotions)
3. Sends them to GPT-4.1-nano to categorize into: Urgent, Action Items, Low Priority, Key Updates
4. Emails the summary back to you

## Setup

### Prerequisites

- Python 3.x
- A Google Cloud project with the Gmail API enabled
- An OpenAI API key

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

1. **Google Cloud credentials** — Download your OAuth client credentials from the [Google Cloud Console](https://console.cloud.google.com/) and save as `credentials.json` in the project root.

2. **Environment variables** — Create a `.env` file:

```
OPENAI_API_KEY=your_openai_api_key
EMAIL=your_email@gmail.com
```

3. **First run** — The first time you run the script, it will open a browser window for Google OAuth. After authorizing, a `token.json` will be created automatically.

### Usage

```bash
python quickstart.py
```
