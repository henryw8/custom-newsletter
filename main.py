#!/usr/bin/env python3
"""
Custom Newsletter - Main Entry Point
====================================

LEARNING OBJECTIVE: Orchestrate a pipeline from config → fetch → format → send.

This script ties everything together. Run it manually for testing:
  python main.py

Or let GitHub Actions run it daily via cron. The flow is:

  1. Load config (interests.yaml)     → What feeds to fetch?
  2. Fetch articles from all feeds    → Get the content
  3. Build HTML + plain text          → Format for email
  4. Send via SMTP                   → Deliver to your inbox

All secrets (SMTP credentials, recipient) come from environment variables,
which GitHub Actions injects from repository secrets.
"""

import os
import sys
from pathlib import Path

# Add project root to path so we can import from src
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Load .env file if it exists (for local development)
from dotenv import load_dotenv
load_dotenv()

from src.newsletter_builder import (
    load_config,
    fetch_all_articles,
    build_html,
    build_plain_text,
)
from src.email_sender import send_newsletter

try:
    from src.mcp_summarizer import summarize_articles
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


def main() -> None:
    # Determine project root (works when run from any directory)
    project_root = Path(__file__).resolve().parent
    os.chdir(project_root)

    config_path = project_root / "config" / "interests.yaml"
    template_dir = project_root / "templates"

    print("Loading configuration...")
    config = load_config(str(config_path))

    print("Fetching articles from feeds...")
    articles = fetch_all_articles(config)
    print(f"Found {len(articles)} articles")

    if not articles:
        print("No articles to send. Check your feed URLs in config/interests.yaml")
        return

    # Summarize via MCP if API key is set (OPENAI_API_KEY or ANTHROPIC_API_KEY)
    summarized_by = None
    if MCP_AVAILABLE and (os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")):
        print("Summarizing articles with MCP...")
        articles = summarize_articles(articles, project_root)
        if os.environ.get("OPENAI_API_KEY"):
            summarized_by = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        else:
            summarized_by = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    elif os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"):
        print("MCP not available (requires Python 3.10+). Using feed summaries.")
    else:
        print("Skipping MCP summarization (set OPENAI_API_KEY or ANTHROPIC_API_KEY to enable)")

    print("Building newsletter...")
    html = build_html(articles, str(template_dir), summarized_by=summarized_by)
    plain = build_plain_text(articles)

    print("Sending email...")
    send_newsletter(html, plain)
    print("Done!")


if __name__ == "__main__":
    main()
