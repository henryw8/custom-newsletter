"""
MCP Server - Article Summarization Tool
=======================================

LEARNING OBJECTIVE: Build an MCP server that exposes tools for AI to use.

MCP (Model Context Protocol) lets you expose capabilities as "tools" that
clients can invoke. This server exposes a summarize_article tool that uses
an LLM to generate concise summaries. The newsletter script acts as an
MCP client, connecting to this server and calling the tool for each article.

Flow:
  Newsletter (client) --stdio--> This server --API--> OpenAI/Anthropic

Run standalone: python -m src.mcp_server
Or the newsletter spawns it as a subprocess and connects via stdio.
"""

import os
import sys

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "newsletter-summarizer",
    instructions="Summarizes news articles for a daily newsletter.",
)


def _call_llm(text: str, max_tokens: int = 150) -> str:
    """
    Call an LLM to summarize text. Supports OpenAI and Anthropic.
    Set OPENAI_API_KEY or ANTHROPIC_API_KEY in the environment.
    """
    # Prefer OpenAI (simpler, widely available)
    if api_key := os.environ.get("OPENAI_API_KEY"):
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {
                        "role": "system",
                        "content": "Summarize the following in 1-2 concise sentences for a newsletter. Be informative and neutral. Do not use markdown formatting, headers, or bullet points — plain prose only.",
                    },
                    {"role": "user", "content": text[:4000]},  # Token limit
                ],
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI error: {e}", file=sys.stderr)
            return ""

    # Fallback to Anthropic
    if api_key := os.environ.get("ANTHROPIC_API_KEY"):
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model=os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
                max_tokens=max_tokens,
                system="Summarize the following in 1-2 concise sentences for a newsletter. Be informative and neutral. Do not use markdown formatting, headers, or bullet points — plain prose only.",
                messages=[{"role": "user", "content": text[:4000]}],
            )
            import re
            text_out = response.content[0].text.strip()
            text_out = re.sub(r"^#+\s*", "", text_out, flags=re.MULTILINE)
            return text_out
        except Exception as e:
            print(f"Anthropic error: {e}", file=sys.stderr)
            return ""

    print("No OPENAI_API_KEY or ANTHROPIC_API_KEY set", file=sys.stderr)
    return ""


@mcp.tool()
def summarize_article(title: str, content: str) -> str:
    """Summarize a news article in 1-2 sentences for a newsletter.

    Args:
        title: The article headline.
        content: The article text or excerpt to summarize (from RSS feed).

    Returns:
        A concise summary suitable for the newsletter, or empty string if summarization fails.
    """
    if not content or not content.strip():
        return title  # No content to summarize, just return title

    combined = f"Title: {title}\n\n{content}"
    summary = _call_llm(combined)
    return summary if summary else content[:200] + ("..." if len(content) > 200 else "")


if __name__ == "__main__":
    # Stdio is the default - client will spawn us and talk via stdin/stdout
    mcp.run(transport="stdio")
