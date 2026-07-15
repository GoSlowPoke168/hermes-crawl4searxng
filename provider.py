"""Crawl4AI web-extract provider — plugin form.

Subclasses :class:`agent.web_search_provider.WebSearchProvider`. Extract-only
— Crawl4AI renders and cleans arbitrary URLs but doesn't run web search, so
``supports_search()`` returns False. Pair with the bundled SearXNG provider
(or any other search-capable backend) for ``web_search`` calls.

Uses Crawl4AI's ``/md`` endpoint, which returns already-filtered markdown as
a plain string — simpler and more reliable than ``/crawl``, whose
``markdown`` field is a nested dict of several markdown variants.

Config keys this provider responds to::

    web:
      extract_backend: "crawl4ai"   # explicit per-capability
      backend: "crawl4ai"           # shared fallback

Env vars::

    CRAWL4AI_URL=http://127.0.0.1:11235
    CRAWL4AI_API_TOKEN=<bearer token your Crawl4AI instance requires>
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from agent.web_search_provider import WebSearchProvider

logger = logging.getLogger(__name__)


def _env_value(name: str) -> str:
    """Return an env var via Hermes' config-aware lookup, falling back to process env."""
    try:
        from hermes_cli.config import get_env_value

        val = get_env_value(name)
    except Exception:
        val = None
    if val is None:
        import os

        val = os.getenv(name, "")
    return (val or "").strip()


class Crawl4AIWebSearchProvider(WebSearchProvider):
    """Extract clean page content via a self-hosted Crawl4AI instance."""

    @property
    def name(self) -> str:
        return "crawl4ai"

    @property
    def display_name(self) -> str:
        return "Crawl4AI"

    def is_available(self) -> bool:
        """Return True when ``CRAWL4AI_URL`` is set."""
        return bool(_env_value("CRAWL4AI_URL"))

    def supports_search(self) -> bool:
        return False

    def supports_extract(self) -> bool:
        return True

    def extract(self, urls: List[str], **kwargs: Any) -> Dict[str, Any]:
        """Fetch clean markdown for each URL via Crawl4AI's ``/md`` endpoint."""
        import httpx

        base_url = _env_value("CRAWL4AI_URL").rstrip("/")
        if not base_url:
            return {"success": False, "error": "CRAWL4AI_URL is not set"}

        token = _env_value("CRAWL4AI_API_TOKEN")
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        results = []
        for url in urls:
            try:
                resp = httpx.post(
                    f"{base_url}/md",
                    json={"url": url, "filter": "fit"},
                    headers=headers,
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPStatusError as exc:
                logger.warning("Crawl4AI HTTP error for %s: %s", url, exc)
                results.append({
                    "url": url,
                    "content": "",
                    "error": f"Crawl4AI returned HTTP {exc.response.status_code}",
                })
                continue
            except httpx.RequestError as exc:
                logger.warning("Crawl4AI request error for %s: %s", url, exc)
                results.append({
                    "url": url,
                    "content": "",
                    "error": f"Could not reach Crawl4AI at {base_url}: {exc}",
                })
                continue
            except Exception as exc:  # noqa: BLE001
                logger.warning("Crawl4AI response parse error for %s: %s", url, exc)
                results.append({
                    "url": url,
                    "content": "",
                    "error": "Could not parse Crawl4AI response",
                })
                continue

            if not data.get("success"):
                results.append({
                    "url": url,
                    "content": "",
                    "error": data.get("error") or "Crawl4AI reported failure",
                })
                continue

            markdown = data.get("markdown", "")
            results.append({
                "url": url,
                "title": "",
                "content": markdown,
                "raw_content": markdown,
                "metadata": {},
            })

        return {"success": True, "data": results}

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Crawl4AI",
            "badge": "free · self-hosted",
            "tag": "Open-source browser-based crawler/extractor. Point CRAWL4AI_URL at your instance.",
            "env_vars": [
                {
                    "key": "CRAWL4AI_URL",
                    "prompt": "Crawl4AI instance URL (e.g. http://localhost:11235)",
                    "url": "https://github.com/unclecode/crawl4ai",
                },
                {
                    "key": "CRAWL4AI_API_TOKEN",
                    "prompt": "Crawl4AI API bearer token",
                    "url": "https://github.com/unclecode/crawl4ai",
                },
            ],
        }
