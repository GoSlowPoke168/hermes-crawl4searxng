#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == '--purge' ]]; then
  echo 'Purge is not supported. Research notes, credentials, service settings and volumes are retained.' >&2
  exit 2
fi
if [[ $# -gt 0 && "${1:-}" != '--help' && "${1:-}" != '-h' ]]; then
  echo 'Use --help for native removal instructions.' >&2
  exit 2
fi
echo 'To stop only this plugin’s managed services while retaining data:'
echo '  hermes crawl4searxng stop'
echo 'Then remove the plugin through Hermes:'
echo '  hermes plugins remove hermes-crawl4searxng'
echo 'Existing external services are not stopped. This script does not remove data.'
