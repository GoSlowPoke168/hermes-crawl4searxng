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

from typing import Any, Dict, List

from agent.web_search_provider import WebSearchProvider

def _env_value(name: str) -> str:
    from agent.secret_scope import get_secret
    return (get_secret(name) or "").strip()


class Crawl4AIWebSearchProvider(WebSearchProvider):
    """Extract clean page content via a self-hosted Crawl4AI instance."""

    def __init__(self, settings=None):
        self.settings = settings or (lambda key, default=None: default)

    def base_url(self):
        return (self.settings("crawl4ai_url", "") or _env_value("CRAWL4AI_URL")).rstrip("/")

    @property
    def name(self) -> str:
        return "crawl4ai"

    @property
    def display_name(self) -> str:
        return "Crawl4AI"

    def is_available(self) -> bool:
        """Return True when ``CRAWL4AI_URL`` is set."""
        return bool(self.base_url())

    def supports_search(self) -> bool:
        return False

    def supports_extract(self) -> bool:
        return True

    def extract(self, urls: List[str], **kwargs: Any) -> List[Dict[str, Any]]:
        """Fetch clean markdown for each URL via Crawl4AI's ``/md`` endpoint."""
        import httpx

        base_url = self.base_url()
        if not base_url:
            return [
                {"url": url, "content": "", "error": "CRAWL4AI_URL is not set"}
                for url in urls
            ]

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
                if not isinstance(data, dict) or not isinstance(data.get("markdown"), str):
                    raise ValueError("Invalid markdown response")
            except httpx.HTTPStatusError as exc:
                results.append({
                    "url": url,
                    "content": "",
                    "error": f"Crawl4AI returned HTTP {exc.response.status_code}",
                })
                continue
            except httpx.RequestError as exc:
                results.append({
                    "url": url,
                    "content": "",
                    "error": "Could not reach Crawl4AI",
                })
                continue
            except (ValueError, TypeError):
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
                    "error": "Crawl4AI reported failure",
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

        return results

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
                    "secret": True,
                    "prompt": "Crawl4AI API bearer token",
                    "url": "https://github.com/unclecode/crawl4ai",
                },
            ],
        }
