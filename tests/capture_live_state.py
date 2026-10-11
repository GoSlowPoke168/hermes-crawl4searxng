"""Capture nonsecret live invariants before/after the authorized reinstall."""
import hashlib
import json
import sys
from pathlib import Path

from hermes_cli.config import load_config_readonly
from hermes_constants import get_hermes_home

home = get_hermes_home()
config = load_config_readonly() or {}
snapshot = {
    'other_plugin_entries': {key: value for key, value in config.get('plugins', {}).get('entries', {}).items() if key != 'hermes-crawl4searxng'},
    'notes': {str(path.relative_to(home / 'knowledge')): hashlib.sha256(path.read_bytes()).hexdigest() for path in (home / 'knowledge').glob('**/*') if path.is_file()},
    'web': config.get('web', {}),
}
# Other settings can contain credential mirrors: compare hashes, never print them.
snapshot['other_plugin_entries'] = hashlib.sha256(json.dumps(snapshot['other_plugin_entries'], sort_keys=True).encode()).hexdigest()
output = Path(sys.argv[1])
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(snapshot, indent=2))
output.chmod(0o600)
print('Recorded plugin-settings hash and research-note hashes; no credential values recorded.')
