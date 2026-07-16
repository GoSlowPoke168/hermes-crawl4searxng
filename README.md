# hermes-crawl4searxng

A [Hermes Agent](https://github.com/NousResearch/hermes-agent) web-search-provider plugin that gives the agent's native `web_search` / `web_extract` tools a fully self-hosted backend:

- **Search** → [SearXNG](https://docs.searxng.org/) (via Hermes' own bundled SearXNG provider — nothing to write here, it just needs `SEARXNG_URL` set).
- **Extract** → [Crawl4AI](https://github.com/unclecode/crawl4ai) (this plugin's contribution — no bundled Hermes provider wraps Crawl4AI).

Unlike a plugin that invents its own custom tool names, this registers a proper `WebSearchProvider` backend via `ctx.register_web_search_provider(...)`, so it plugs directly into the `web_search`/`web_extract` tools every model already knows about — no naming collisions with Hermes' built-in `web` toolset.

Also bundles:
- `save_finding` — a small tool that writes a cited research note to `~/.hermes/knowledge/`.
- `deep-research` skill — a short workflow guide (search → extract → cite → save).

## What `install.sh` does

Wires everything into Hermes and provisions both backing services, in one of two modes:

| | `--symlink` (default) | `--bundled` |
|---|---|---|
| Docker configs live at | `~/docker/{crawl4ai,searxng}` | `<hermes-plugins-dir>/hermes-crawl4searxng/docker/` |
| Plugin dir is | a symlink back to this repo | a real, self-contained copy of it |
| `git pull` here takes effect | immediately (same files) | after re-running `install.sh --bundled` (re-copies code, never touches secrets) |
| Good for | active development on this repo | a single self-contained directory with nothing living outside it |

1. Deploys Crawl4AI — generates `CRAWL4AI_API_TOKEN`/`SECRET_KEY` via `openssl rand -hex 32` on first run only.
2. Deploys SearXNG — seeds a minimal `settings.yml` with a generated secret key on first run only; **never touches an existing `settings.yml`**, so your own customizations are always preserved.
3. Syncs `SEARXNG_URL` / `CRAWL4AI_URL` / `CRAWL4AI_API_TOKEN` into your Hermes `.env` (located via `hermes config env-path`, not assumed to be `~/.hermes`).
4. Symlinks (or, in `--bundled` mode, copies) the plugin into your Hermes plugins directory (located via `hermes config path`), enables it, sets `web.extract_backend: crawl4ai`, and restarts the gateway.
5. If found, disables (does not delete) a superseded `evey-research`-style plugin at `hermes-plugins/evey-research`.

If neither the `hermes` CLI nor `~/.hermes` can be found, Docker services are still provisioned and the script prints the exact values/commands to wire Hermes up manually.

It's idempotent — re-run it any time (e.g. after `git pull`) to pick up compose-file changes without touching secrets or your custom config.

```bash
git clone <this-repo-url> ~/Projects/hermes-crawl4searxng
cd ~/Projects/hermes-crawl4searxng
./install.sh              # or: ./install.sh --bundled
```

> **Switching modes on the same machine**: both modes' Docker Compose files use the same fixed container names (`crawl4ai`, `searxng-core`, `searxng-valkey`), since Docker containers are identified globally by name, not by which directory their compose file lives in. Running `install.sh` in the *other* mode on a host that already has containers running will re-point those same containers (and regenerate their secrets) to the new location rather than creating an independent second stack — `install.sh` warns before doing this. If you want a clean switch, run `uninstall.sh` for the old mode first.

### Installing via `hermes plugins install` instead

The repo root doubles as the plugin directory, so it also works with Hermes' own installer:

```bash
hermes plugins install <owner>/hermes-crawl4searxng
```

This handles the `plugin.yaml`/env-var prompts, but **does not** provision Docker — run `install.sh` (from a clone, or from `~/.hermes/plugins/hermes-crawl4searxng/install.sh` after installing) separately for that.

## Requirements

- Docker + Docker Compose v2
- `openssl` (secret generation)
- Hermes Agent CLI on `PATH`

## Uninstalling

Auto-detects which mode you installed with — no flag needed.

```bash
./uninstall.sh          # stops containers, disables/unlinks (or in bundled mode, keeps) the plugin — keeps all data & secrets
./uninstall.sh --purge   # also deletes Docker volumes, generated .env files, settings.yml, and (bundled mode) the plugin's own directory (asks to confirm)
```

## Configuration reference

| Env var | Where | Purpose |
|---|---|---|
| `SEARXNG_URL` | `~/.hermes/.env` | Tells Hermes' bundled SearXNG provider where to search |
| `CRAWL4AI_URL` | `~/.hermes/.env` | Tells this plugin's provider where to extract from |
| `CRAWL4AI_API_TOKEN` | `~/.hermes/.env` + `~/docker/crawl4ai/.env` | Bearer token — must match on both sides (install.sh keeps them in sync) |

## Troubleshooting

- **Plugin not showing up**: `hermes plugins list | grep hermes-crawl4searxng`, then check `~/.hermes/logs/errors.log` for `Failed to load plugin`.
- **web_extract errors**: confirm `docker ps` shows `crawl4ai` healthy, and that the token in `~/docker/crawl4ai/.env` matches `~/.hermes/.env`.
- **web_search errors**: confirm `curl http://127.0.0.1:8080/search?q=test&format=json` returns results — if not, this is Hermes' bundled SearXNG provider, not this plugin.

## License

MIT
