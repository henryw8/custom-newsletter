"""
MCP Client - Summarize Articles via MCP
=======================================

LEARNING OBJECTIVE: Use an MCP client to invoke tools on an MCP server.

This module connects to our MCP server (mcp_server.py) as a subprocess and
calls the summarize_article tool for each article. The server runs the LLM
call; the client just orchestrates the tool invocations.

Architecture:
  main.py (sync)
    -> mcp_summarizer.summarize_articles(articles)  # runs async event loop
         -> spawns mcp_server.py
         -> calls session.call_tool("summarize_article", {...})
         -> returns articles with AI summaries
"""

import asyncio
import os
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _extract_text_from_result(result) -> str:
    """Extract content text from MCP CallToolResult."""
    if hasattr(result, "content") and result.content:
        for block in result.content:
            if hasattr(block, "text"):
                return block.text
            if isinstance(block, dict) and "text" in block:
                return block["text"]
    return ""


async def _summarize_with_mcp(articles: list[dict], server_path: Path) -> list[dict]:
    """Connect to MCP server and summarize each article."""
    server_params = StdioServerParameters(
        command="python3",
        args=[str(server_path)],
        env=os.environ.copy(),  # Pass API keys to the server subprocess
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            for i, article in enumerate(articles):
                title = article.get("title", "Untitled")
                content = article.get("summary") or article.get("link", "")

                try:
                    result = await session.call_tool(
                        "summarize_article",
                        {"title": title, "content": content},
                    )
                    summary = _extract_text_from_result(result)
                    if summary:
                        article["summary"] = summary
                except Exception as e:
                    print(f"Warning: MCP summarization failed for '{title[:40]}...': {e}")

    return articles


def summarize_articles(articles: list[dict], project_root: Path) -> list[dict]:
    """
    Summarize articles using the MCP server. Runs async in a new event loop.

    Skips MCP if OPENAI_API_KEY and ANTHROPIC_API_KEY are both unset.

    Args:
        articles: List of article dicts with title, summary, link.
        project_root: Path to project root (where mcp_server.py lives).

    Returns:
        Same articles with 'summary' updated to AI-generated summaries.
    """
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        return articles

    server_path = project_root / "src" / "mcp_server.py"
    if not server_path.exists():
        return articles

    return asyncio.run(_summarize_with_mcp(articles, server_path))
