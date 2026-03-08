"""
Newsletter Builder Module
=========================

LEARNING OBJECTIVE: Separate data fetching from presentation.

This module takes the raw article data and builds an HTML email. We use
Jinja2 templating - the same engine used by Flask, Django, and Ansible.
Templates let us:
  - Keep HTML structure separate from Python logic
  - Reuse layouts and make styling changes without touching code
  - Support multiple output formats (HTML, plain text) from one template
"""

import yaml
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .feed_fetcher import fetch_feed


def load_config(config_path: str = "config/interests.yaml") -> dict:
    """
    Load the interests configuration from YAML.

    YAML is human-readable and easy to edit - perfect for config files.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    with open(path) as f:
        return yaml.safe_load(f)


def fetch_all_articles(config: dict) -> list[dict]:
    """
    Fetch articles from all configured feeds, grouped by interest.
    """
    all_articles = []

    for interest in config.get("interests", []):
        name = interest.get("name", "Uncategorized")
        for feed_config in interest.get("feeds", []):
            url = feed_config.get("url")
            if not url:
                continue
            max_items = feed_config.get("max_items", 5)

            articles = fetch_feed(url, max_items=max_items)
            for article in articles:
                article["category"] = name
                all_articles.append(article)

    # Sort by date (newest first) - articles without dates go to end
    def sort_key(a):
        pub = a.get("published") or ""
        return (0, pub) if pub else (1, "")

    all_articles.sort(key=sort_key, reverse=True)
    return all_articles


def build_html(articles: list[dict], template_dir: str = "templates") -> str:
    """
    Render the newsletter as HTML using a Jinja2 template.
    """
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("newsletter.html")

    # Group articles by category for nicer display
    by_category: dict[str, list] = {}
    for article in articles:
        cat = article.get("category", "Other")
        by_category.setdefault(cat, []).append(article)

    html = template.render(
        articles=articles,
        by_category=by_category,
        date=__import__("datetime").datetime.now().strftime("%A, %B %d, %Y"),
    )
    return html


def build_plain_text(articles: list[dict]) -> str:
    """
    Build a simple plain-text fallback (for email clients that don't support HTML).
    """
    lines = ["Your Daily Newsletter", "=" * 40, ""]
    current_cat = None
    for a in articles:
        if a.get("category") != current_cat:
            current_cat = a.get("category")
            lines.append(f"\n## {current_cat}\n")
        lines.append(f"- {a['title']}")
        lines.append(f"  {a['link']}")
        lines.append("")
    return "\n".join(lines)
