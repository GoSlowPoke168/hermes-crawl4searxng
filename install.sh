#!/usr/bin/env bash
# hermes-crawl4searxng installer
#
# Idempotent: safe to re-run. Never overwrites an existing .env or an
# existing SearXNG core-config/settings.yml — those hold secrets/customizations.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_HOME="${DOCKER_HOME:-$HOME/docker}"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
PLUGIN_NAME="hermes-crawl4searxng"

log() { printf '==> %s\n' "$1"; }
warn() { printf 'WARNING: %s\n' "$1" >&2; }

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "ERROR: '$1' is required but not found in PATH." >&2; exit 1; }
}

require docker
require openssl
if ! docker compose version >/dev/null 2>&1; then
  echo "ERROR: 'docker compose' (v2 plugin) is required." >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# 1. Crawl4AI
# ---------------------------------------------------------------------------
log "Provisioning Crawl4AI under ${DOCKER_HOME}/crawl4ai"
mkdir -p "$DOCKER_HOME/crawl4ai"
cp "$REPO_DIR/docker/crawl4ai/docker-compose.yml" "$DOCKER_HOME/crawl4ai/docker-compose.yml"

if [ ! -f "$DOCKER_HOME/crawl4ai/.env" ]; then
  log "Generating Crawl4AI secrets (openssl rand -hex 32)"
  CRAWL4AI_API_TOKEN="$(openssl rand -hex 32)"
  CRAWL4AI_SECRET_KEY="$(openssl rand -hex 32)"
  cat > "$DOCKER_HOME/crawl4ai/.env" <<EOF
CRAWL4AI_API_TOKEN=${CRAWL4AI_API_TOKEN}
SECRET_KEY=${CRAWL4AI_SECRET_KEY}
EOF
  chmod 600 "$DOCKER_HOME/crawl4ai/.env"
else
  log "Crawl4AI .env already exists — leaving secrets untouched"
fi

log "Starting Crawl4AI"
( cd "$DOCKER_HOME/crawl4ai" && docker compose up -d )

# ---------------------------------------------------------------------------
# 2. SearXNG
# ---------------------------------------------------------------------------
log "Provisioning SearXNG under ${DOCKER_HOME}/searxng"
mkdir -p "$DOCKER_HOME/searxng/core-config"
cp "$REPO_DIR/docker/searxng/docker-compose.yml" "$DOCKER_HOME/searxng/docker-compose.yml"

if [ ! -f "$DOCKER_HOME/searxng/.env" ]; then
  log "Seeding SearXNG .env from defaults"
  cp "$REPO_DIR/docker/searxng/.env.example" "$DOCKER_HOME/searxng/.env"
else
  log "SearXNG .env already exists — leaving untouched"
fi

if [ ! -f "$DOCKER_HOME/searxng/core-config/settings.yml" ]; then
  log "Rendering SearXNG settings.yml with a freshly generated secret_key"
  SEARXNG_SECRET_KEY="$(openssl rand -hex 16)"
  sed "s/__GENERATED_SECRET_KEY__/${SEARXNG_SECRET_KEY}/" \
    "$REPO_DIR/docker/searxng/core-config/settings.yml.template" \
    > "$DOCKER_HOME/searxng/core-config/settings.yml"
else
  log "SearXNG core-config/settings.yml already exists — leaving your custom config untouched"
fi

log "Starting SearXNG"
( cd "$DOCKER_HOME/searxng" && docker compose up -d )

# ---------------------------------------------------------------------------
# 3. Health checks
# ---------------------------------------------------------------------------
log "Waiting for services to become healthy..."
for i in $(seq 1 30); do
  c4_status="$(docker inspect --format '{{.State.Health.Status}}' hermes-crawl4ai 2>/dev/null || echo "unknown")"
  sx_status="$(docker inspect --format '{{.State.Status}}' searxng-core 2>/dev/null || echo "unknown")"
  if [ "$c4_status" = "healthy" ] && [ "$sx_status" = "running" ]; then
    break
  fi
  sleep 2
done
log "Crawl4AI health: ${c4_status:-unknown} | SearXNG status: ${sx_status:-unknown}"

# ---------------------------------------------------------------------------
# 4. Sync Hermes-side env (~/.hermes/.env) — read-and-sync, never blind-generate
# ---------------------------------------------------------------------------
CRAWL4AI_TOKEN_VALUE="$(grep '^CRAWL4AI_API_TOKEN=' "$DOCKER_HOME/crawl4ai/.env" | cut -d= -f2-)"
SEARXNG_HOST_VALUE="$(grep '^SEARXNG_HOST=' "$DOCKER_HOME/searxng/.env" 2>/dev/null | cut -d= -f2- || true)"
SEARXNG_PORT_VALUE="$(grep '^SEARXNG_PORT=' "$DOCKER_HOME/searxng/.env" 2>/dev/null | cut -d= -f2- || true)"
SEARXNG_HOST_VALUE="${SEARXNG_HOST_VALUE:-127.0.0.1}"
SEARXNG_PORT_VALUE="${SEARXNG_PORT_VALUE:-8080}"

HERMES_ENV="$HERMES_HOME/.env"
mkdir -p "$HERMES_HOME"
touch "$HERMES_ENV"

set_env_var() {
  local key="$1" value="$2"
  if grep -q "^${key}=" "$HERMES_ENV" 2>/dev/null; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$HERMES_ENV"
  else
    printf '%s=%s\n' "$key" "$value" >> "$HERMES_ENV"
  fi
}

log "Syncing SEARXNG_URL / CRAWL4AI_URL / CRAWL4AI_API_TOKEN into ${HERMES_ENV}"
set_env_var "SEARXNG_URL" "http://${SEARXNG_HOST_VALUE}:${SEARXNG_PORT_VALUE}"
set_env_var "CRAWL4AI_URL" "http://127.0.0.1:11235"
set_env_var "CRAWL4AI_API_TOKEN" "$CRAWL4AI_TOKEN_VALUE"

# ---------------------------------------------------------------------------
# 5. Plugin activation
# ---------------------------------------------------------------------------
require hermes

PLUGIN_LINK="$HERMES_HOME/plugins/$PLUGIN_NAME"
mkdir -p "$HERMES_HOME/plugins"
if [ -L "$PLUGIN_LINK" ]; then
  ln -sfn "$REPO_DIR" "$PLUGIN_LINK"
  log "Updated existing symlink $PLUGIN_LINK -> $REPO_DIR"
elif [ -e "$PLUGIN_LINK" ]; then
  warn "$PLUGIN_LINK already exists and is not a symlink — leaving it untouched. Remove it manually if you want install.sh to manage it."
else
  ln -s "$REPO_DIR" "$PLUGIN_LINK"
  log "Symlinked $PLUGIN_LINK -> $REPO_DIR"
fi

log "Enabling plugin in Hermes"
hermes plugins enable "$PLUGIN_NAME" || warn "hermes plugins enable failed — check 'hermes plugins list' manually"

log "Setting web.extract_backend = crawl4ai"
hermes config set web.extract_backend crawl4ai || warn "hermes config set failed — set it manually in ~/.hermes/config.yaml"

# ---------------------------------------------------------------------------
# 6. Retire the old evey-research plugin (config-level disable only — never
#    touches ~/.hermes/plugins/hermes-plugins/, which holds 30+ other plugins)
# ---------------------------------------------------------------------------
if hermes plugins list 2>/dev/null | grep -q "evey-research"; then
  log "Disabling superseded plugin evey-research (config-level only — does not touch its files)"
  hermes plugins disable "evey-research" || warn "Could not disable evey-research automatically — run 'hermes plugins disable evey-research' manually"
fi

log "Restarting Hermes gateway"
hermes gateway restart || warn "Could not restart the gateway automatically — run 'hermes gateway restart' yourself"

log "Done. Verify with: hermes plugins list | grep $PLUGIN_NAME"
