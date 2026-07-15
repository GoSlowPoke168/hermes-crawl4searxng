---
name: deep-research
description: Structured web research workflow — search, extract, cite, and optionally save findings to the knowledge library.
---

# Deep Research

Use this skill when a request needs real, current, cited information from the
web rather than answering from memory — e.g. "what's the latest on X",
"find and summarize", "research Y and give me sources".

## Workflow

1. **Search** with `web_search` for the topic. Issue more than one query if
   the topic is broad or the first results look thin (try a rephrase, or a
   more specific/more general variant).
2. **Extract** with `web_extract` on the 2-4 most relevant URLs from the
   search results — don't just repeat the search snippets, pull the actual
   page content so claims are grounded in the source, not a summary of a
   summary.
3. **Synthesize** an answer from the extracted content. Every non-obvious
   claim should be traceable to one of the extracted URLs.
4. **Cite** sources inline or in a short list at the end — always include
   the URLs you actually extracted from, not just search-result links you
   didn't read.
5. **Save (optional)** — if the user is building up a knowledge base or
   asks you to remember/save the research, call `save_finding` with a
   short topic slug, the synthesized markdown content, and the source URLs.
   This writes a citation-backed note to `~/.hermes/knowledge/`.

## Pitfalls

- Don't call `web_extract` on every search result — pick the ones that
  actually look relevant to avoid burning time/tokens on pages you won't use.
- If `web_extract` fails for a URL (dead link, paywall, JS-only page),
  don't silently drop the claim — say so, and fall back to the search
  snippet with a caveat that it's unverified.
- Don't call `save_finding` unless the user wants the research persisted —
  it writes a file, not a scratch note.
