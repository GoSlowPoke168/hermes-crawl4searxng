"""Run after installed Hermes bootstrap: HOME [--save-test-note].

Uses native discovery, web wrappers and the registry. Saves only when explicitly
requested in a disposable home; never writes a test note into the main profile.
"""
import asyncio
import json
import os
from pathlib import Path
import sys

home = Path(sys.argv[1]).resolve()
os.environ['HERMES_HOME'] = str(home)
from hermes_constants import set_hermes_home_override
set_hermes_home_override(home)
from agent.secret_scope import build_profile_secret_scope, set_secret_scope
set_secret_scope(build_profile_secret_scope(home), profile_home=str(home))
from hermes_cli.plugins import get_plugin_manager
manager = get_plugin_manager()
manager.discover_and_load()
skill = manager.find_plugin_skill('hermes-crawl4searxng:deep-research')
assert skill and skill.is_file(), 'Installed skill missing'
from tools.web_tools import web_search_tool, web_extract_tool
search = json.loads(web_search_tool('Hermes Agent', limit=2))
assert search.get('success') and search.get('data', {}).get('web'), 'Native search failed'
extraction = json.loads(asyncio.run(web_extract_tool(['https://example.com', 'https://127.0.0.1'])))
results = extraction.get('results', [])
assert len(results) == 2 and results[0].get('content', '').strip() and not results[0].get('error'), 'Native extraction failed'
assert results[1].get('error'), 'Blocked private URL was not isolated'
print('Native discovery, explicit skill registration, search and mixed-result extraction passed.')
if '--save-test-note' in sys.argv:
    assert '.test-artifacts' in home.parts, 'Test notes require a disposable home'
    from tools.registry import registry
    saved = registry.dispatch('save_finding', {'topic': 'Native UTF-8 smoke', 'content': 'Verified café 日本語', 'sources': ['https://example.com']})
    saved = json.loads(saved) if isinstance(saved, str) else saved
    path = Path(saved.get('path', ''))
    assert saved.get('status') == 'saved' and path.is_relative_to(home / 'knowledge')
    assert 'café 日本語' in path.read_text(encoding='utf-8')
    print('Native save_finding wrote a UTF-8 note only inside the disposable home.')
