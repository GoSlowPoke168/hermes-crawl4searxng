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
import tempfile
from pathlib import Path
from typing import Any, Dict

from .provider import Crawl4AIWebSearchProvider

SAVE_FINDING_SCHEMA = {
    "name": "save_finding",
    "description": (
        "Save a research finding to the knowledge library with proper citation. "
        "Findings are saved in the active Hermes home's knowledge directory. "
        "Saving the same topic replaces its previous note."
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
        if not isinstance(topic, str) or not isinstance(content, str):
            raise ValueError("topic and content must be strings")
        if not isinstance(sources, list) or any(not isinstance(source, str) for source in sources):
            raise ValueError("sources must be a list of URLs")

        safe_name = re.sub(r"[^\w\-]", "-", topic.lower()).strip("-")
        if not safe_name:
            safe_name = "untitled"

        from hermes_constants import get_hermes_home
        knowledge_dir = get_hermes_home() / "knowledge"
        os.makedirs(knowledge_dir, exist_ok=True)

        filepath = os.path.join(knowledge_dir, f"{safe_name}.md")

        doc = f"# {topic}\n\n"
        doc += f"*Researched: {time.strftime('%Y-%m-%d %H:%M %Z')}*\n\n"
        doc += content + "\n"

        if sources:
            doc += "\n## Sources\n\n"
            for s in sources:
                doc += f"- {s}\n"

        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=knowledge_dir, delete=False) as f:
                temporary = f.name
                f.write(doc)
            os.replace(temporary, filepath)
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)

        return json.dumps({
            "status": "saved",
            "path": filepath,
            "topic": topic,
            "chars": len(doc),
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def register(ctx) -> None:
    from .cli import register_cli
    ctx.register_web_search_provider(Crawl4AIWebSearchProvider(ctx.get_config))
    register_cli(ctx)

    if ctx.get_config("save_finding_enabled", True):
        ctx.register_tool(
            name="save_finding",
            toolset="hermes_crawl4searxng",
            schema=SAVE_FINDING_SCHEMA,
            handler=save_handler,
        )

    if ctx.get_config("deep_research_enabled", True):
        skill_md = Path(__file__).parent / "skills" / "deep-research" / "SKILL.md"
        if skill_md.exists():
            ctx.register_skill(
                "deep-research",
                skill_md,
                description="Structured web research workflow: search, extract, cite, save",
            )
