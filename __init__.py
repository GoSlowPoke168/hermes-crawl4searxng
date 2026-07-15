"""hermes-crawl4searxng — Crawl4AI web-extract provider for Hermes.

Registers a WebSearchProvider backend so the agent's native web_extract
tool can be routed to a self-hosted Crawl4AI instance (pair with the
bundled SearXNG provider, already active via SEARXNG_URL, for web_search).

Also bundles a small save_finding tool for writing cited research notes to
the knowledge library, and an optional deep-research skill.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict

from .provider import Crawl4AIWebSearchProvider

SAVE_FINDING_SCHEMA = {
    "name": "save_finding",
    "description": (
        "Save a research finding to the knowledge library with proper citation. "
        "Findings are saved as markdown files in ~/.hermes/knowledge/."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "Topic name (used as filename)",
            },
            "content": {
                "type": "string",
                "description": "Research content in markdown format",
            },
            "sources": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of source URLs",
            },
        },
        "required": ["topic", "content"],
    },
}


def save_handler(args: Dict[str, Any], **kwargs: Any) -> str:
    try:
        topic = args.get("topic", "untitled")
        content = args.get("content", "")
        sources = args.get("sources", [])

        safe_name = re.sub(r"[^\w\-]", "-", topic.lower()).strip("-")
        if not safe_name:
            safe_name = "untitled"

        knowledge_dir = os.path.expanduser("~/.hermes/knowledge")
        os.makedirs(knowledge_dir, exist_ok=True)

        filepath = os.path.join(knowledge_dir, f"{safe_name}.md")

        doc = f"# {topic}\n\n"
        doc += f"*Researched: {time.strftime('%Y-%m-%d %H:%M %Z')}*\n\n"
        doc += content + "\n"

        if sources:
            doc += "\n## Sources\n\n"
            for s in sources:
                doc += f"- {s}\n"

        with open(filepath, "w") as f:
            f.write(doc)

        return json.dumps({
            "status": "saved",
            "path": filepath,
            "topic": topic,
            "chars": len(doc),
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def register(ctx) -> None:
    ctx.register_web_search_provider(Crawl4AIWebSearchProvider())

    ctx.register_tool(
        name="save_finding",
        toolset="hermes_crawl4searxng",
        schema=SAVE_FINDING_SCHEMA,
        handler=save_handler,
    )

    try:
        skill_md = Path(__file__).parent / "skills" / "deep-research" / "SKILL.md"
        if skill_md.exists():
            ctx.register_skill(
                "deep-research",
                skill_md,
                description="Structured web research workflow: search, extract, cite, save",
            )
    except AttributeError:
        pass
