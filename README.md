# hermes-crawl4searxng

A [Hermes Agent](https://github.com/NousResearch/hermes-agent) plugin that gives the agent's native `web_search` / `web_extract` tools a fully self-hosted backend:

- **Search** → [SearXNG](https://docs.searxng.org/) — via Hermes' own bundled provider; nothing to write here, it just needs `SEARXNG_URL` set.
- **Extract** → [Crawl4AI](https://github.com/unclecode/crawl4ai) — this plugin's contribution; no bundled Hermes provider wraps Crawl4AI.

It registers a real `WebSearchProvider` via `ctx.register_web_search_provider(...)`, so it plugs straight into the tools every model already knows — no custom tool names, no collisions with Hermes' built-in `web` toolset.

Also bundles:

- **`save_finding` tool** — writes a cited research note to `~/.hermes/knowledge/<topic-slug>.md` from a `topic`, `content` (markdown), and optional `sources` (URLs, appended as a `## Sources` list).
- **`deep-research` skill** — a search → extract → synthesize → cite → optionally save workflow. See [`skills/deep-research/SKILL.md`](skills/deep-research/SKILL.md).

## Install

```bash
git clone https://github.com/GoSlowPoke168/hermes-crawl4searxng.git
cd hermes-crawl4searxng
./install.sh
```

This starts Crawl4AI + SearXNG in Docker, generates secrets on first run, and wires the plugin into Hermes. It's idempotent — re-run it any time (e.g. after `git pull`) to pick up compose-file changes, and it never touches existing secrets or your custom SearXNG config.

### Install modes

`--bundled` is the default; `--symlink` is for active development on this repo.

| | `--bundled` (default) | `--symlink` |
|---|---|---|
| Plugin dir | real copy in `~/.hermes/plugins/` | symlink → your clone |
| Docker configs | `<plugin-dir>/docker/` | `~/docker/` |
| Code changes apply | after re-running `install.sh` | immediately |
| Best for | install and forget | developing this plugin |

**Switching modes on the same machine:**

- Both modes use the same fixed container names (`crawl4ai`, `searxng-core`, `searxng-valkey`) — Docker identifies containers globally by name, not by which directory their compose file lives in.
- Re-running `install.sh` in the *other* mode re-points those same containers (and regenerates their secrets) rather than creating an independent second stack. It warns before doing this.
- For a clean switch, run `uninstall.sh` for the old mode first.

### Installing via `hermes plugins install`

The repo root doubles as the plugin directory, so Hermes' own installer works too:

```bash
hermes plugins install GoSlowPoke168/hermes-crawl4searxng
```

This handles the `plugin.yaml` / env-var prompts, but **does not** provision Docker — run `install.sh` separately for that (from a clone, or from `~/.hermes/plugins/hermes-crawl4searxng/install.sh` after installing).

## What `install.sh` does

1. Deploys Crawl4AI — generates `CRAWL4AI_API_TOKEN` / `SECRET_KEY` via `openssl rand -hex 32`, first run only.
2. Deploys SearXNG — seeds a minimal `settings.yml` with a generated secret key, first run only; **never touches an existing `settings.yml`**, so your customizations are always preserved.
3. Syncs `SEARXNG_URL` / `CRAWL4AI_URL` / `CRAWL4AI_API_TOKEN` into your Hermes `.env` (located via `hermes config env-path`, not assumed to be `~/.hermes`).
4. Installs the plugin into your Hermes plugins directory (located via `hermes config path`), enables it, sets `web.extract_backend: crawl4ai`, and restarts the gateway.

If neither the `hermes` CLI nor `~/.hermes` can be found, Docker services are still provisioned and the script prints the exact values and commands to wire Hermes up manually.

## Requirements

- Docker + Docker Compose v2
- `openssl` (secret generation)
- Hermes Agent CLI on `PATH`

## Uninstalling

Auto-detects which mode you installed with — no flag needed.

```bash
./uninstall.sh           # stops containers, disables and unlinks/removes the plugin — keeps all data & secrets
./uninstall.sh --purge   # also deletes volumes, generated .env files, settings.yml, and (bundled mode) the plugin's own directory — asks first
```

## Configuration reference

| Env var | Where | Purpose |
|---|---|---|
| `SEARXNG_URL` | `~/.hermes/.env` | Where Hermes' bundled SearXNG provider searches |
| `CRAWL4AI_URL` | `~/.hermes/.env` | Where this plugin extracts from |
| `CRAWL4AI_API_TOKEN` | `~/.hermes/.env` + Crawl4AI `.env` | Bearer token — must match on both sides (`install.sh` keeps them in sync) |

The Crawl4AI `.env` lives at `~/docker/crawl4ai/.env` in `--symlink` mode, or `~/.hermes/plugins/hermes-crawl4searxng/docker/crawl4ai/.env` in `--bundled` mode.

## Troubleshooting

- **`web_extract` errors** — confirm `docker ps` shows `crawl4ai` healthy, and that the token in its `.env` (path above) matches `~/.hermes/.env`.
- **`web_search` errors** — confirm `curl 'http://127.0.0.1:8080/search?q=test&format=json'` returns results. If not, that's Hermes' bundled SearXNG provider, not this plugin.

## Support the Project
If you find this plugin useful, please leave a star on GitHub or consider supporting its development!

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/T5T725W4FX)

## License

[![GitHub License](https://img.shields.io/github/license/goslowpoke168/hermes-crawl4searxng?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmZmZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0ibHVjaWRlIGx1Y2lkZS1zY2FsZSI+PHBhdGggZD0ibTE2IDE2IDMtOCAzIDhjLS44Ny42NS0xLjkyIDEtMyAxcy0yLjEzLS4zNS0zLTFaIi8+PHBhdGggZD0ibTIgMTYgMy04IDMgOGMtLjg3LjY1LTEuOTIgMS0zIDFzLTIuMTMtLjM1LTMtMVoiLz48cGF0aCBkPSJNNyAyMWgxMCIvPjxwYXRoIGQ9Ik0xMiAzdjE4Ii8+PHBhdGggZD0iTTMgN2gyYzIgMCA1LTEgNy0yIDIgMSA1IDIgNyAyaDIiLz48L3N2Zz4=)](https://github.com/GoSlowPoke168/hermes-crawl4searxng/blob/master/LICENSE)
