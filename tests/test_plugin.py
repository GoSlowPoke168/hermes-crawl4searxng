import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tested_plugin', ROOT / '__init__.py', submodule_search_locations=[str(ROOT)])
plugin = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = plugin
spec.loader.exec_module(plugin)
provider = sys.modules['tested_plugin.provider']


def context(home, settings=None):
    ctx = Mock()
    ctx.get_config.side_effect = lambda key, default=None: (settings or {}).get(key, default)
    state = {}
    ctx.state.get.side_effect = lambda key, default=None: state.get(key, default)
    ctx.state.set.side_effect = lambda key, value: state.__setitem__(key, value)
    ctx.state.data_dir = home / 'plugin-data'
    return ctx


class PluginTests(unittest.TestCase):
    def test_manifest_capabilities_shape(self):
        import hermes_yaml as yaml
        manifest = yaml.safe_load((ROOT / 'plugin.yaml').read_text())
        self.assertIsInstance(manifest.get('capabilities', []), list)

    def test_scoped_miss_never_falls_back(self):
        with patch('agent.secret_scope.get_secret', return_value=None), patch('hermes_cli.config.get_env_value', return_value=None), patch.dict(os.environ, {'CRAWL4AI_API_TOKEN': 'wrong-profile'}):
            self.assertEqual(provider._env_value('CRAWL4AI_API_TOKEN'), '')

    def test_scope_error_propagates(self):
        with patch('agent.secret_scope.get_secret', side_effect=RuntimeError('scope')), patch('hermes_cli.config.get_env_value', return_value=None):
            with self.assertRaises(RuntimeError):
                provider._env_value('CRAWL4AI_API_TOKEN')

    def test_configured_provider_and_bad_response_isolated(self):
        with patch('agent.secret_scope.get_secret', return_value='fixture-secret'), patch('httpx.post') as post:
            post.side_effect = [Mock(json=lambda: []), Mock(json=lambda: {'success': True, 'markdown': 'verified'})]
            instance = provider.Crawl4AIWebSearchProvider(lambda key, default=None: 'http://fixture' if key == 'crawl4ai_url' else default)
            result = instance.extract(['bad', 'good'])
            self.assertIn('error', result[0])
            self.assertEqual(result[1]['content'], 'verified')
            self.assertEqual(post.call_args.args[0], 'http://fixture/md')
            self.assertEqual(post.call_args.kwargs['headers']['Authorization'], 'Bearer fixture-secret')

    def test_optional_registrations(self):
        for tool, skill in [(True, True), (False, True), (True, False), (False, False)]:
            ctx = context(Path('/unused'), {'save_finding_enabled': tool, 'deep_research_enabled': skill})
            plugin.register(ctx)
            self.assertEqual(ctx.register_tool.called, tool)
            self.assertEqual(ctx.register_skill.called, skill)
            self.assertTrue(ctx.register_cli_command.called)

    def test_notes_use_active_home_and_atomic_replace(self):
        with tempfile.TemporaryDirectory() as temp, patch('hermes_constants.get_hermes_home', return_value=Path(temp)):
            outside = Path(temp) / 'outside'
            outside.write_text('preserve')
            knowledge = Path(temp) / 'knowledge'
            knowledge.mkdir()
            (knowledge / 'topic.md').symlink_to(outside)
            result = json.loads(plugin.save_handler({'topic': 'Topic', 'content': '東京', 'sources': ['https://example.com']}))
            self.assertEqual(result['status'], 'saved')
            self.assertIn('東京', (knowledge / 'topic.md').read_text())
            self.assertEqual(outside.read_text(), 'preserve')

    def test_invalid_note_does_not_create_directory(self):
        with tempfile.TemporaryDirectory() as temp, patch('hermes_constants.get_hermes_home', return_value=Path(temp)):
            for args in [{'topic': [], 'content': 'x'}, {'topic': 't', 'content': []}, {'topic': 't', 'content': 'x', 'sources': [4]}]:
                self.assertIn('error', json.loads(plugin.save_handler(args)))
            self.assertFalse((Path(temp) / 'knowledge').exists())


if __name__ == '__main__':
    unittest.main()
