#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  -h|--help)
    echo 'Install: hermes plugins install GoSlowPoke168/hermes-crawl4searxng --enable'
    echo 'Configure: hermes crawl4searxng setup'
    exit 0 ;;
  '') ;;
  *)
    echo 'Legacy flags (--bundled, --standalone, --symlink) are no longer supported.' >&2
    echo 'Install through Hermes, then select existing endpoints in setup to retain legacy Docker services.' >&2
    exit 2 ;;
esac
if ! command -v hermes >/dev/null || ! hermes crawl4searxng --help >/dev/null 2>&1; then
  echo 'Install and enable the plugin first:' >&2
  echo '  hermes plugins install GoSlowPoke168/hermes-crawl4searxng --enable' >&2
  echo 'Then run: hermes crawl4searxng setup' >&2
  exit 1
fi
exec hermes crawl4searxng setup
