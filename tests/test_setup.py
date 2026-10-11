import importlib
import io
import socket
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch
from test_plugin import context


class DeploymentTests(unittest.TestCase):
    def module(self):
        return importlib.import_module('tested_plugin.deployment')

    def test_preserves_token_and_custom_settings(self):
        mod = self.module()
        with tempfile.TemporaryDirectory() as temp, patch.object(mod, 'compose'):
            root = Path(temp)
            mod.provision_service('crawl4ai', root / 'crawl', 'test', token='first')
            env = root / 'crawl' / '.env'
            before = env.read_bytes()
            mod.provision_service('crawl4ai', root / 'crawl', 'test', token='second')
            self.assertEqual(env.read_bytes(), before)
            self.assertEqual(env.stat().st_mode & 0o777, 0o600)
            mod.provision_service('searxng', root / 'search', 'test')
            settings = root / 'search' / 'core-config' / 'settings.yml'
            settings.write_text('custom settings')
            mod.provision_service('searxng', root / 'search', 'test')
            self.assertEqual(settings.read_text(), 'custom settings')

    def test_secret_symlink_rejected(self):
        mod = self.module()
        with tempfile.TemporaryDirectory() as temp, patch.object(mod, 'compose'):
            root = Path(temp)
            outside = root / 'outside'
            outside.write_text('unchanged')
            (root / '.env').symlink_to(outside)
            with self.assertRaises(ValueError):
                mod.provision_service('crawl4ai', root, 'test', token='fixture')
            self.assertEqual(outside.read_text(), 'unchanged')

    def test_collision_is_not_adopted(self):
        mod = self.module()
        with tempfile.TemporaryDirectory() as temp, socket.socket() as listener, patch('subprocess.run'):
            listener.bind(('127.0.0.1', 0))
            with patch.dict(mod.PORTS, {'crawl4ai': listener.getsockname()[1]}):
                with self.assertRaisesRegex(RuntimeError, 'occupied'):
                    mod.preflight_service('crawl4ai', Path(temp) / 'new', 'test', False)
            with self.assertRaisesRegex(ValueError, 'ownership'):
                mod.preflight_service('crawl4ai', Path(temp), 'test', False)

    def test_unknown_service_rejected(self):
        mod = self.module()
        with self.assertRaises(ValueError):
            mod.provision_service('other', Path('/unused'), 'test')

    def test_compose_argv_and_stop_retains_volumes(self):
        mod = self.module()
        with patch('subprocess.run') as run:
            mod.stop_service(Path('/tmp/space here'), 'test')
            argv = run.call_args.args[0]
            self.assertIn('/tmp/space here/docker-compose.yml', argv)
            self.assertEqual(argv[-1], 'down')
            self.assertNotIn('-v', argv)
            self.assertFalse(run.call_args.kwargs.get('shell', False))
            run.side_effect = subprocess.CalledProcessError(1, argv, stderr='fixture-secret')
            with self.assertRaisesRegex(RuntimeError, 'Docker Compose') as caught:
                mod.stop_service(Path('/tmp/space here'), 'test')
            self.assertNotIn('fixture-secret', str(caught.exception))


class WizardTests(unittest.TestCase):
    def module(self):
        return importlib.import_module('tested_plugin.cli')

    def test_every_service_combination(self):
        mod = self.module()
        for crawl in ['1', '2']:
            for search in ['1', '2', '3']:
                with self.subTest(crawl=crawl, search=search), tempfile.TemporaryDirectory() as temp:
                    ctx = context(Path(temp))
                    answers = [crawl] + (['https://crawl.example'] if crawl == '2' else [])
                    answers += [search] + (['https://search.example'] if search == '2' else [])
                    answers += ['', '', 'y']
                    output = io.StringIO()
                    with patch('sys.stdin.isatty', return_value=True), patch('builtins.input', side_effect=answers), patch.object(mod, 'getpass', return_value='fixture-secret'), patch.object(mod, '_env_value', return_value=''), patch.object(mod, 'preflight_service'), patch.object(mod, 'provision_service') as provision, patch.object(mod, 'check_services'), patch.object(mod, 'save_provider_env_credential'), patch.object(mod, 'require_writable'), patch.object(mod, 'set_routing') as routing, redirect_stdout(output):
                        self.assertEqual(mod.run_setup(ctx), 0)
                    self.assertEqual(provision.call_count, (crawl == '1') + (search == '1'))
                    self.assertEqual(routing.call_args.args, (search != '3',))
                    self.assertNotIn('fixture-secret', output.getvalue())
                    values = dict(call.args for call in ctx.set_config.call_args_list)
                    self.assertTrue(values['save_finding_enabled'])
                    self.assertTrue(values['deep_research_enabled'])

    def test_cancel_and_no_terminal_have_no_changes(self):
        mod = self.module()
        for tty, answers, expected in [(False, [], 1), (True, [EOFError()], 1), (True, ['', '', 'n', 'n', 'n'], 0)]:
            ctx = context(Path('/unused'))
            with patch('sys.stdin.isatty', return_value=tty), patch('builtins.input', side_effect=answers), patch.object(mod, '_env_value', return_value=''), patch.object(mod, 'provision_service') as provision, patch.object(mod, 'save_provider_env_credential') as save, redirect_stdout(io.StringIO()):
                self.assertEqual(mod.run_setup(ctx), expected)
            provision.assert_not_called()
            save.assert_not_called()
            ctx.set_config.assert_not_called()

    def test_failed_probe_preserves_routes_and_settings(self):
        mod = self.module()
        ctx = context(Path('/unused'))
        with patch('sys.stdin.isatty', return_value=True), patch('builtins.input', side_effect=['2', 'https://crawl.example', '3', '', '', 'y']), patch.object(mod, 'getpass', return_value='fixture-secret'), patch.object(mod, '_env_value', return_value=''), patch.object(mod, 'require_writable'), patch.object(mod, 'check_services', side_effect=RuntimeError('Service check failed')), patch.object(mod, 'set_routing') as routing, patch.object(mod, 'save_provider_env_credential') as save, redirect_stdout(io.StringIO()):
            self.assertEqual(mod.run_setup(ctx), 1)
        routing.assert_not_called()
        save.assert_not_called()
        ctx.set_config.assert_not_called()

    def test_url_validation(self):
        mod = self.module()
        for value in ['', 'file:///tmp/x', 'http://u:p@host', 'http://host:99999', 'https://host?q=x', 'https://host#frag', 'http://', 'https://host/with space']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                mod.validate_url(value)
        self.assertEqual(mod.validate_url('https://host/api/'), 'https://host/api')

    def test_managed_setting_preflight(self):
        mod = self.module()
        with patch('hermes_cli.config.is_managed', return_value=False), patch('hermes_cli.config.require_env_writable'), patch('hermes_cli.managed_scope.is_key_managed', side_effect=lambda key: key.endswith('.deep_research_enabled')):
            with self.assertRaisesRegex(RuntimeError, 'administrator-managed'):
                mod.require_writable(False)

    def test_routing_explicitly_preserves_default_profile(self):
        mod = self.module()
        with patch('subprocess.run') as run, patch('hermes_cli.main.explicit_cli_profile', return_value='default'):
            mod.set_routing(True)
            for call in run.call_args_list:
                self.assertEqual(call.args[0][:4], ['hermes', '--profile', 'default', 'config'])

    def test_managed_external_managed_preserves_credentials(self):
        mod = self.module()
        with tempfile.TemporaryDirectory() as temp:
            ctx = context(Path(temp))
            credentials = {'CRAWL4AI_API_TOKEN': ''}
            required = {'http://127.0.0.1:11235': None, 'https://external': 'external-token'}
            def save(key, value):
                credentials[key] = value
            def provision(service, directory, project, token=''):
                directory.mkdir(parents=True, exist_ok=True)
                env = directory / '.env'
                if not env.exists():
                    env.write_text(token)
                    required['http://127.0.0.1:11235'] = token
            def probe(url, token, search):
                if token != required[url]:
                    raise RuntimeError('Service check returned HTTP 401')
            sequences = [['1', '3', '', '', 'y'], ['2', 'https://external', '3', '', '', 'y'], ['1', '3', '', '', 'y']]
            with patch('sys.stdin.isatty', return_value=True), patch.object(mod, '_env_value', side_effect=lambda key: credentials.get(key, '')), patch.object(mod, 'getpass', return_value='external-token'), patch.object(mod, 'preflight_service'), patch.object(mod, 'provision_service', side_effect=provision), patch.object(mod, 'check_services', side_effect=probe), patch.object(mod, 'save_provider_env_credential', side_effect=save), patch.object(mod, 'require_writable'), patch.object(mod, 'set_routing'), patch.object(mod.time, 'sleep'), redirect_stdout(io.StringIO()):
                for answers in sequences:
                    with patch('builtins.input', side_effect=answers):
                        self.assertEqual(mod.run_setup(ctx), 0)
            self.assertEqual(credentials['CRAWL4AI_API_TOKEN'], required['http://127.0.0.1:11235'])

    def test_failed_managed_startup_keeps_external_token(self):
        mod = self.module()
        with tempfile.TemporaryDirectory() as temp:
            ctx = context(Path(temp))
            credentials = {'CRAWL4AI_API_TOKEN': 'external-token'}
            def save(key, value):
                credentials[key] = value
            def provision(service, directory, project, token=''):
                directory.mkdir(parents=True)
                raise RuntimeError('Docker Compose failed')
            with patch('sys.stdin.isatty', return_value=True), patch('builtins.input', side_effect=['1', '3', '', '', 'y']), patch.object(mod, '_env_value', side_effect=lambda key: credentials.get(key, '')), patch.object(mod, 'preflight_service'), patch.object(mod, 'provision_service', side_effect=provision), patch.object(mod, 'save_provider_env_credential', side_effect=save), patch.object(mod, 'require_writable'), patch.object(mod, 'set_routing') as routing, redirect_stdout(io.StringIO()):
                self.assertEqual(mod.run_setup(ctx), 1)
            self.assertEqual(credentials['CRAWL4AI_API_TOKEN'], 'external-token')
            self.assertIn('crawl4ai', ctx.state.get('managed_services'))
            routing.assert_not_called()
            ctx.set_config.assert_not_called()

    def test_stop_refuses_forged_ownership(self):
        mod = self.module()
        ctx = context(Path('/unused'))
        with patch.object(mod, 'stop_service') as stop, redirect_stdout(io.StringIO()):
            self.assertEqual(mod.run_stop(ctx), 0)
            ctx.state.set('managed_services', {'crawl4ai': {'directory': '/other', 'project': 'other'}})
            self.assertEqual(mod.run_stop(ctx), 1)
            stop.assert_not_called()

    def test_probe_rejects_auth_failure_and_accepts_empty_search(self):
        mod = self.module()
        import httpx
        with patch('httpx.post', return_value=httpx.Response(401, request=httpx.Request('POST', 'http://fixture/md'))):
            with self.assertRaisesRegex(RuntimeError, '401'):
                mod.check_services('http://fixture', '', None)
        with patch('httpx.post', return_value=httpx.Response(200, json={'success': True, 'markdown': 'text'}, request=httpx.Request('POST', 'http://fixture/md'))), patch('httpx.get', return_value=httpx.Response(200, json={'results': []}, request=httpx.Request('GET', 'http://fixture/search'))):
            mod.check_services('http://fixture', '', 'http://fixture')
