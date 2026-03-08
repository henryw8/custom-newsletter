# Custom Newsletter

A pedagogical project that emails you a personalized daily newsletter based on your interests. Runs automatically every morning via GitHub Actions cron.

## What You'll Learn

| Concept | Where to See It |
|---------|-----------------|
| **RSS/Atom feeds** | `src/feed_fetcher.py` – how blogs publish machine-readable updates |
| **HTTP & parsing** | `feed_fetcher.py` – `requests` + `feedparser` |
| **MCP (Model Context Protocol)** | `src/mcp_server.py` + `src/mcp_summarizer.py` – AI summarization via tools |
| **Templating** | `src/newsletter_builder.py` + `templates/newsletter.html` – Jinja2 |
| **SMTP** | `src/email_sender.py` – sending email with Python's stdlib |
| **Cron scheduling** | `.github/workflows/daily-newsletter.yml` – GitHub Actions |
| **Secrets management** | Workflow env vars from GitHub Secrets |

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  interests.yaml │────▶│  feed_fetcher.py  │────▶│ mcp_summarizer  │
│  (your config)  │     │  (RSS/Atom)       │     │ (MCP client)    │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                           ▲                               │
                    ┌──────┴──────┐                        │ call_tool
                    │ RSS feeds   │                        ▼
                    └─────────────┘               ┌─────────────────┐
                                                 │ mcp_server.py   │
                                                 │ (summarize tool)│
                                                 └────────┬────────┘
                                                          │ LLM API
                                                          ▼
                                                 ┌─────────────────┐
                                                 │ newsletter_     │
                                                 │ builder.py      │
                                                 └────────┬────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │ email_sender.py │
                                                 └────────┬────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │  Your inbox     │
                                                 └─────────────────┘
```

**Pipeline:** Config → Fetch → **MCP Summarize** → Format → Send

---

## Quick Start

### 1. Clone and install

```bash
cd custom-newsletter
pip install -r requirements.txt
```

**Note:** MCP (AI summarization) requires Python 3.10+. Without it, the newsletter uses feed excerpts.

### 2. Customize your interests

Edit `config/interests.yaml` – add RSS feeds for topics you care about. Most blogs have `/feed` or `/rss` in the URL.

### 3. Set up email (for local testing)

```bash
export SMTP_USER="your@gmail.com"
export SMTP_PASSWORD="your-app-password"   # Gmail: use App Password, not regular password
export NEWSLETTER_RECIPIENT="your@gmail.com"
```

**Gmail App Password:** [Google Account](https://myaccount.google.com/) → Security → 2-Step Verification → App passwords.

### 4. (Optional) Enable MCP summarization

Set one of these to get AI-generated summaries instead of raw feed excerpts:

```bash
export OPENAI_API_KEY="sk-..."      # or
export ANTHROPIC_API_KEY="sk-ant-..."
```

Without an API key, the newsletter uses the feed's built-in summary/description.

### 5. Run locally

```bash
python main.py
```

---

## GitHub Actions Setup (Automation)

To run the newsletter every morning automatically:

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial newsletter setup"
git remote add origin https://github.com/YOUR_USERNAME/custom-newsletter.git
git push -u origin main
```

### 2. Add repository secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|--------|-------------|
| `SMTP_USER` | Your email (e.g., `you@gmail.com`) |
| `SMTP_PASSWORD` | Gmail App Password or SendGrid API key |
| `NEWSLETTER_RECIPIENT` | Where to send (often same as `SMTP_USER`) |

Optional for MCP summarization (AI summaries):

| Secret | Description |
|--------|-------------|
| `OPENAI_API_KEY` | OpenAI API key (uses gpt-4o-mini by default) |
| `ANTHROPIC_API_KEY` | Anthropic API key (uses Claude Haiku by default) |

Optional for non-Gmail:

| Secret | Default |
|--------|---------|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |

### 3. Schedule

The workflow runs at **12:00 UTC** daily. To change the time, edit `.github/workflows/daily-newsletter.yml`:

```yaml
schedule:
  - cron: "0 12 * * *"   # minute hour day month weekday
```

**Cron quick reference:**
- `0 12 * * *` = noon UTC daily
- `0 7 * * *` = 7am UTC (2am EST)
- `30 6 * * 1-5` = 6:30am UTC, weekdays only

### 4. Manual test

**Actions → Daily Newsletter → Run workflow** to trigger immediately.

---

## Project Structure

```
custom-newsletter/
├── main.py                 # Entry point – orchestrates the pipeline
├── requirements.txt
├── config/
│   └── interests.yaml      # Your feeds – edit this!
├── src/
│   ├── feed_fetcher.py     # Fetches & parses RSS/Atom
│   ├── mcp_server.py       # MCP server – summarize_article tool (LLM)
│   ├── mcp_summarizer.py   # MCP client – calls server for each article
│   ├── newsletter_builder.py  # Loads config, builds HTML
│   └── email_sender.py     # Sends via SMTP
├── templates/
│   └── newsletter.html     # Jinja2 email template
└── .github/
    └── workflows/
        └── daily-newsletter.yml   # Cron + manual trigger
```

---

## Extending the Project

Ideas for learning more:

1. **Add more content sources** – APIs (e.g., Hacker News, Reddit), web scraping
2. **Filter by keywords** – Only include articles matching certain terms
3. **Deduplicate** – Same story from multiple feeds
4. **Add a preview mode** – `python main.py --dry-run` to print HTML without sending
5. **Use SendGrid/Mailgun** – Free tiers, often easier than Gmail for automation

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "SMTP_USER must be set" | Add secrets in GitHub repo settings |
| Gmail "Less secure app" error | Use an App Password, not your normal password |
| Workflow doesn't run | GitHub may disable scheduled workflows after 60 days of no commits |
| No articles | Check feed URLs in `interests.yaml` – test them in a browser |
| MCP summarization fails | Ensure OPENAI_API_KEY or ANTHROPIC_API_KEY is set; check API quota |

---

## License

MIT – use and modify freely.
