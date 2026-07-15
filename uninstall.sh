#!/usr/bin/env bash
# hermes-crawl4searxng uninstaller
#
# By default: stops containers, disables and unlinks/removes the plugin, but
# keeps all data/secrets/custom config intact so re-running install.sh
# restores the exact same setup. Pass --purge to also delete Docker volumes,
# the generated .env files, the SearXNG settings.yml, and (bundled mode only)
# the plugin's own copied directory.
#
# Auto-detects which install mode was used (symlink vs bundled) by looking
# at what's actually on disk — no flag needed.
set -euo pipefail

PLUGIN_NAME="hermes-crawl4searxng"
PURGE=0

for arg in "$@"; do
  case "$arg" in
    --purge) PURGE=1 ;;
  esac
done

log() { printf '==> %s\n' "$1"; }
warn() { printf 'WARNING: %s\n' "$1" >&2; }

# ---------------------------------------------------------------------------
# Locate the live Hermes install the same way install.sh does.
# ---------------------------------------------------------------------------
HERMES_CLI_AVAILABLE=0
HERMES_PLUGINS_DIR=""

if command -v hermes >/dev/null 2>&1; then
  HERMES_CLI_AVAILABLE=1
  if detected_config_path="$(hermes config path 2>/dev/null)" && [ -n "$detected_config_path" ]; then
    HERMES_PLUGINS_DIR="$(dirname "$detected_config_path")/plugins"
  fi
fi
if [ -n "${HERMES_HOME:-}" ]; then
  HERMES_PLUGINS_DIR="$HERMES_HOME/plugins"
fi
if [ -z "$HERMES_PLUGINS_DIR" ] && [ -d "$HOME/.hermes" ]; then
  HERMES_PLUGINS_DIR="$HOME/.hermes/plugins"
fi

if [ "$HERMES_CLI_AVAILABLE" -eq 1 ]; then
  log "Disabling plugin"
  hermes plugins disable "$PLUGIN_NAME" || true
fi

if [ -z "$HERMES_PLUGINS_DIR" ]; then
  warn "Could not locate your Hermes plugins directory — skipping plugin removal/unlink. Remove it manually if needed."
  PLUGIN_TARGET_DIR=""
else
  PLUGIN_TARGET_DIR="$HERMES_PLUGINS_DIR/$PLUGIN_NAME"
fi

# ---------------------------------------------------------------------------
# Detect mode from what's actually on disk: a symlink means --symlink mode
# (Docker configs live under ~/docker/); a real directory containing its own
# docker/ subfolder means --bundled mode (Docker configs live inside it).
# ---------------------------------------------------------------------------
MODE="unknown"
if [ -n "$PLUGIN_TARGET_DIR" ] && [ -L "$PLUGIN_TARGET_DIR" ]; then
  MODE="symlink"
  DOCKER_HOME="${DOCKER_HOME:-$HOME/docker}"
elif [ -n "$PLUGIN_TARGET_DIR" ] && [ -d "$PLUGIN_TARGET_DIR/docker" ]; then
  MODE="bundled"
  DOCKER_HOME="$PLUGIN_TARGET_DIR/docker"
else
  # Nothing on disk to detect from (already removed, or never installed via
  # this script) — fall back to the symlink-mode default location so
  # `docker compose down` still has somewhere to look.
  DOCKER_HOME="${DOCKER_HOME:-$HOME/docker}"
fi
log "Detected mode: $MODE"

if [ "$MODE" = "symlink" ] && [ -n "$PLUGIN_TARGET_DIR" ]; then
  log "Removing symlink $PLUGIN_TARGET_DIR"
  rm "$PLUGIN_TARGET_DIR"
fi

if [ "$PURGE" -eq 1 ]; then
  read -r -p "This will delete Docker volumes, generated secrets, and your custom SearXNG settings.yml. Type 'yes' to confirm: " confirm
  if [ "$confirm" = "yes" ]; then
    log "Purging Crawl4AI (containers + volumes + .env)"
    [ -d "$DOCKER_HOME/crawl4ai" ] && ( cd "$DOCKER_HOME/crawl4ai" && docker compose down -v || true )
    rm -f "$DOCKER_HOME/crawl4ai/.env"
    log "Purging SearXNG (containers + volumes + .env + settings.yml)"
    [ -d "$DOCKER_HOME/searxng" ] && ( cd "$DOCKER_HOME/searxng" && docker compose down -v || true )
    rm -f "$DOCKER_HOME/searxng/.env"
    rm -f "$DOCKER_HOME/searxng/core-config/settings.yml"
    if [ "$MODE" = "bundled" ] && [ -n "$PLUGIN_TARGET_DIR" ]; then
      log "Removing bundled plugin directory $PLUGIN_TARGET_DIR"
      rm -rf "$PLUGIN_TARGET_DIR"
    fi
  else
    log "Purge cancelled"
  fi
else
  log "Stopping containers (data/secrets preserved — pass --purge to wipe them)"
  [ -d "$DOCKER_HOME/crawl4ai" ] && ( cd "$DOCKER_HOME/crawl4ai" && docker compose down || true )
  [ -d "$DOCKER_HOME/searxng" ] && ( cd "$DOCKER_HOME/searxng" && docker compose down || true )
  if [ "$MODE" = "bundled" ]; then
    log "Bundled plugin directory kept at $PLUGIN_TARGET_DIR (pass --purge to remove it)"
  fi
fi

log "Done. Re-run install.sh any time to restore this setup."
