#!/usr/bin/env bash
# hermes-crawl4searxng uninstaller
#
# By default: stops containers, disables and unlinks the plugin, but keeps
# all data/secrets/custom config intact so re-running install.sh restores
# the exact same setup. Pass --purge to also delete Docker volumes, the
# generated .env files, and the SearXNG settings.yml.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_HOME="${DOCKER_HOME:-$HOME/docker}"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
PLUGIN_NAME="hermes-crawl4searxng"
PURGE=0

for arg in "$@"; do
  case "$arg" in
    --purge) PURGE=1 ;;
  esac
done

log() { printf '==> %s\n' "$1"; }

log "Disabling plugin"
command -v hermes >/dev/null 2>&1 && hermes plugins disable "$PLUGIN_NAME" || true

PLUGIN_LINK="$HERMES_HOME/plugins/$PLUGIN_NAME"
if [ -L "$PLUGIN_LINK" ]; then
  log "Removing symlink $PLUGIN_LINK"
  rm "$PLUGIN_LINK"
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
  else
    log "Purge cancelled"
  fi
else
  log "Stopping containers (data/secrets preserved — pass --purge to wipe them)"
  [ -d "$DOCKER_HOME/crawl4ai" ] && ( cd "$DOCKER_HOME/crawl4ai" && docker compose down || true )
  [ -d "$DOCKER_HOME/searxng" ] && ( cd "$DOCKER_HOME/searxng" && docker compose down || true )
fi

log "Done. Re-run install.sh any time to restore this setup."
