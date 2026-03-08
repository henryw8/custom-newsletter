"""
Feed Fetcher Module
===================

LEARNING OBJECTIVE: Understand how to fetch and parse RSS/Atom feeds.

RSS (Really Simple Syndication) and Atom are XML-based formats that websites
use to publish updates. When you "subscribe" to a blog, you're typically
subscribing to its feed. This module fetches those feeds and extracts the
structured content (title, link, summary, date).

Data flow:
  1. Take a feed URL
  2. HTTP GET the URL (requests)
  3. Parse the XML into structured data (feedparser)
  4. Return a list of article dicts
"""

import feedparser
import requests
from datetime import datetime
from typing import Optional


def fetch_feed(
    url: str,
    max_items: int = 5,
    timeout: int = 10,
) -> list[dict]:
    """
    Fetch and parse an RSS/Atom feed, returning the latest articles.

    Args:
        url: The feed URL (e.g., https://example.com/feed)
        max_items: Maximum number of articles to return per feed
        timeout: HTTP request timeout in seconds

    Returns:
        List of dicts with keys: title, link, summary, published, source
    """
    articles = []

    try:
        # Step 1: Fetch the raw XML content
        # We use requests instead of feedparser's built-in fetch so we can
        # control timeout and handle errors explicitly
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()  # Raise exception for 4xx/5xx

        # Step 2: Parse the XML with feedparser
        # feedparser handles both RSS and Atom formats transparently
        parsed = feedparser.parse(response.content)

        # Step 3: Extract entries (each entry is an article/post)
        entries = parsed.entries[:max_items]

        # Step 4: Normalize the data into a consistent structure
        # Different feeds use different field names (e.g., summary vs description)
        feed_title = parsed.feed.get("title", "Unknown Source")

        for entry in entries:
            # Parse publication date - feeds use various formats
            published = _parse_date(
                entry.get("published") or entry.get("updated"), entry=entry
            )

            articles.append({
                "title": entry.get("title", "Untitled"),
                "link": entry.get("link", ""),
                "summary": _get_summary(entry),
                "published": published,
                "source": feed_title,
            })

    except requests.RequestException as e:
        # Log but don't crash - we'll skip this feed and continue
        print(f"Warning: Could not fetch {url}: {e}")
    except Exception as e:
        print(f"Warning: Error parsing feed {url}: {e}")

    return articles


def _get_summary(entry) -> str:
    """
    Extract a text summary from an entry.
    Feeds vary: some use 'summary', others 'description' or 'content'.
    """
    summary = entry.get("summary") or entry.get("description") or ""
    if not summary and "content" in entry:
        content = entry["content"]
        if content:
            summary = content[0].get("value", "")[:500]
    # Strip HTML tags for plain-text fallback
    if summary and "<" in summary:
        import re
        summary = re.sub(r"<[^>]+>", "", summary)
    return (summary[:300] + "...") if len(summary) > 300 else summary


def _parse_date(date_str: Optional[str], entry: Optional[dict] = None) -> Optional[str]:
    """
    Convert feed date to a human-readable format.
    Feed dates can be in RFC 2822, ISO 8601, or other formats.
    feedparser provides 'published_parsed' or 'updated_parsed' as struct_time.
    """
    # Prefer feedparser's pre-parsed struct_time if available
    if entry:
        parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if parsed:
            try:
                dt = datetime(*parsed[:6])
                return dt.strftime("%b %d, %Y")
            except (TypeError, ValueError):
                pass
    if not date_str:
        return None
    try:
        parsed = feedparser._parse_date(date_str)
        if parsed:
            dt = datetime(*parsed[:6])
            return dt.strftime("%b %d, %Y")
    except Exception:
        pass
    return date_str  # Fallback to raw string
