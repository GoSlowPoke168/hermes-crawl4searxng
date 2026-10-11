# hermes-crawl4searxng

A [Hermes Agent](https://github.com/NousResearch/hermes-agent) plugin that uses SearXNG and Crawl4AI to search the web and read webpages through your own services. This gives Hermes web access without relying on a paid search or scraping API, while keeping you in control of the services it uses.

A terminal setup wizard connects existing instances or deploys Docker, with optional tools for deep research and saving cited notes.

- **Search** → [SearXNG](https://docs.searxng.org/), through Hermes's native `web_search`.
- **Extract** → [Crawl4AI](https://github.com/unclecode/crawl4ai), through Hermes's native `web_extract`.

Also bundles:

- **`save_finding` tool** — saves cited Markdown notes in your active Hermes home's `knowledge/` directory. Saving the same topic replaces its previous note.
- **`deep-research` skill** — search → read sources → synthesize → cite → optionally save. See [the skill](skills/deep-research/SKILL.md).

## Install

Requires **Hermes 0.21.6+**. Docker deployments also need Docker + Compose v2, with Docker daemon access for your user.

```bash
hermes plugins install GoSlowPoke168/hermes-crawl4searxng --enable
hermes crawl4searxng setup
```

The terminal wizard can deploy Docker, connect your own services, or keep your current search provider. Search and extraction are configured independently; both optional extras default to enabled.

Installation and setup are separate. Restart existing Hermes sessions afterward.
No purchased Crawl4AI API key is needed; Docker setup generates a local token.

## Use

Search and read webpages through Hermes normally. For deep research:

```bash
hermes chat --skills hermes-crawl4searxng:deep-research
```

Ask for research with inline citations. To keep a note, ask Hermes to use `save_finding`.
Citation quality depends on the model.

## Uninstalling

```bash
hermes crawl4searxng stop                  # stop managed containers; keep data
hermes plugins remove hermes-crawl4searxng # remove the plugin; keep notes
```

Plugin removal alone does not stop containers. External services are left alone.

## Configuration reference

### Existing services and advanced setup

Run `hermes crawl4searxng setup` again to change your configuration.

| Variable | Purpose |
|---|---|
| `SEARXNG_URL` | Search endpoint |
| `CRAWL4AI_URL` | Extraction endpoint |
| `CRAWL4AI_API_TOKEN` | Your Crawl4AI server's bearer token, if required |

Legacy environment configuration remains supported. The wizard stores settings
and credentials through Hermes. For an existing server, blank token input keeps
the current token; enter `-` for no token.

Managed services use local ports **11235** and **8080**. If your old containers
already use these ports, select **existing instances**. Legacy installation modes
and `--purge` are no longer supported.

If Hermes runs in Docker, use **existing instances** with URLs reachable from its container; `localhost` points to that container.

Setup needs an interactive terminal and Hermes's `in_process` plugin isolation.
Search queries go to SearXNG and its engines; extraction sends the URL and token
to your crawler. Managed setup starts background containers. No telemetry is added.

## Troubleshooting

- **`web_extract` errors** — check your Crawl4AI endpoint and bearer token.
- **`web_search` errors** — check that SearXNG allows JSON results: `curl 'http://127.0.0.1:8080/search?q=test&format=json'`.

## Platform support

| Platform or setup | Status |
|---|---|
| Linux ARM64, existing services | Tested live |
| Linux ARM64, managed Docker | Experimental; partial live coverage |
| Mixed services / keep current search | Experimental; fixture tests only |
| Linux x86-64, macOS, WSL2; Hermes in Docker | Experimental; untested live |
| Native Windows | Unverified |

```bash
hermes --run-module unittest discover -s tests -v
bash -n install.sh uninstall.sh
hermes plugins validate . --install-deps
```
## Troubleshooting

- **`web_extract` errors** — confirm `docker ps` shows `crawl4ai` healthy, and that the token in its `.env` (path above) matches `~/.hermes/.env`.
- **`web_search` errors** — confirm `curl 'http://127.0.0.1:8080/search?q=test&format=json'` returns results. If not, that's Hermes' bundled SearXNG provider, not this plugin.

## Support the Project
If you find this plugin useful, please leave a star on GitHub or consider supporting its development!

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/T5T725W4FX)

## License

[![GitHub License](https://img.shields.io/github/license/goslowpoke168/hermes-crawl4searxng?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmZmZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0ibHVjaWRlIGx1Y2lkZS1zY2FsZSI+PHBhdGggZD0ibTE2IDE2IDMtOCAzIDhjLS44Ny42NS0xLjkyIDEtMyAxcy0yLjEzLS4zNS0zLTFaIi8+PHBhdGggZD0ibTIgMTYgMy04IDMgOGMtLjg3LjY1LTEuOTIgMS0zIDFzLTIuMTMtLjM1LTMtMVoiLz48cGF0aCBkPSJNNyAyMWgxMCIvPjxwYXRoIGQ9Ik0xMiAzdjE4Ii8+PHBhdGggZD0iTTMgN2gyYzIgMCA1LTEgNy0yIDIgMSA1IDIgNyAyaDIiLz48L3N2Zz4=)](https://github.com/GoSlowPoke168/hermes-crawl4searxng/blob/master/LICENSE)
