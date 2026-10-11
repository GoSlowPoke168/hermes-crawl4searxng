"""Interactive setup through Hermes's configuration and credential routes."""
import secrets
import subprocess
import sys
import time
from getpass import getpass
from pathlib import Path
from urllib.parse import urlsplit

from hermes_cli.credential_lifecycle import save_provider_env_credential
from .deployment import PORTS, preflight_service, project_name, provision_service, stop_service
from .provider import _env_value

MANAGED_TOKEN = 'CRAWL4AI_MANAGED_API_TOKEN'


def validate_url(value):
    parsed = urlsplit(value)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment or any(ord(c) <= 32 for c in value):
        raise ValueError('Use an HTTP(S) URL without credentials, query, fragment, or spaces')
    parsed.port  # Validate the port before storing it.
    return value.rstrip('/')


def choice(label, options, default):
    print(label)
    for index, option in enumerate(options, 1):
        print(f'  {index}. {option}')
    while True:
        value = input(f'Choice [{default}]: ').strip() or str(default)
        if value in [str(i) for i in range(1, len(options) + 1)]:
            return int(value)
        print('Choose one of the numbers above.')


def ask_url(label, default):
    if default:
        try:
            default = validate_url(default)
        except ValueError:
            default = ''
    while True:
        try:
            return validate_url(input(f'{label} URL' + (f' [{default}]' if default else '') + ': ').strip() or default)
        except ValueError:
            print('Use a valid HTTP(S) URL without embedded credentials.')


def yes(label, default=True):
    while True:
        answer = input(f'{label} [{"Y/n" if default else "y/N"}]: ').strip().lower()
        if answer in ('', 'y', 'yes', 'n', 'no'):
            return default if not answer else answer in ('y', 'yes')


def managed_record(ctx, service):
    directory = ctx.state.data_dir / 'deployment' / service
    return {'directory': str(directory), 'project': project_name(directory)}


def ownership(ctx):
    records = ctx.state.get('managed_services', {})
    if not isinstance(records, dict) or any(service not in PORTS or record != managed_record(ctx, service) for service, record in records.items()):
        raise ValueError('Managed-service ownership is invalid; no containers were stopped or adopted')
    return records.copy()


def check_services(crawl4ai_url, token, searxng_url):
    import httpx
    try:
        response = httpx.post(crawl4ai_url + '/md', json={'url': 'https://example.com', 'filter': 'fit'}, headers={'Authorization': 'Bearer ' + token} if token else {}, timeout=45)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or not data.get('success') or not isinstance(data.get('markdown'), str) or not data['markdown'].strip():
            raise ValueError('No extracted markdown')
        if searxng_url:
            response = httpx.get(searxng_url + '/search', params={'q': 'Hermes Agent', 'format': 'json'}, timeout=30)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict) or not isinstance(data.get('results'), list):
                raise ValueError('No search result list')
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f'Service check returned HTTP {exc.response.status_code}; check the endpoint and bearer token.') from None
    except (httpx.RequestError, ValueError, TypeError):
        raise RuntimeError('Service check failed: service is unreachable or returned an invalid response.') from None


def require_writable(search, managed=False):
    from hermes_cli.config import is_managed, require_env_writable
    from hermes_cli.managed_scope import is_key_managed
    keys = ['web.extract_backend'] + [f'plugins.entries.hermes-crawl4searxng.settings.{key}' for key in ('crawl4ai_url', 'save_finding_enabled', 'deep_research_enabled')]
    if search:
        keys.append('web.search_backend')
    if is_managed() or any(is_key_managed(key) for key in keys):
        raise RuntimeError('Configuration is administrator-managed; ask the administrator to configure this plugin.')
    for key in ['CRAWL4AI_URL', 'CRAWL4AI_API_TOKEN'] + (['SEARXNG_URL'] if search else []) + ([MANAGED_TOKEN] if managed else []):
        require_env_writable(key, 'set')


def set_routing(search):
    from hermes_cli.main import explicit_cli_profile
    profile = explicit_cli_profile()
    command = ['hermes'] + (['--profile', profile] if profile is not None else [])
    for key, value in [('web.extract_backend', 'crawl4ai')] + ([('web.search_backend', 'searxng')] if search else []):
        subprocess.run([*command, 'config', 'set', key, value], capture_output=True, check=True, timeout=30)


def run_setup(ctx):
    if not sys.stdin.isatty():
        print('Setup requires a terminal. Run hermes crawl4searxng setup interactively.')
        return 1
    try:
        records = ownership(ctx)
        crawl_default = ctx.get_config('crawl4ai_url', '') or _env_value('CRAWL4AI_URL')
        search_default = _env_value('SEARXNG_URL')
        crawl = choice('Crawl4AI', ['Deploy Docker', 'Use existing instance'], 1 if 'crawl4ai' in records or not crawl_default else 2)
        crawl_url = 'http://127.0.0.1:11235' if crawl == 1 else ask_url('Crawl4AI', crawl_default)
        old_token = _env_value('CRAWL4AI_API_TOKEN')
        if crawl == 1:
            token = _env_value(MANAGED_TOKEN)
            if not token and 'crawl4ai' in records:
                token = getpass('Existing managed token is missing from Hermes; enter its current bearer token: ').strip()
                if not token:
                    raise ValueError('Existing managed token is required; its service secret file is retained unchanged.')
            token = token or old_token or secrets.token_hex(32)
        else:
            token = getpass('Bearer token (blank keeps current; - clears it): ').strip() or old_token
        if token == '-':
            token = ''
        search = choice('Search', ['Deploy SearXNG Docker', 'Use existing SearXNG', 'Keep current search provider'], 1 if 'searxng' in records or not search_default else 2)
        search_url = 'http://127.0.0.1:8080' if search == 1 else ask_url('SearXNG', search_default) if search == 2 else None
        save = yes('Enable save_finding?', ctx.get_config('save_finding_enabled', True))
        research = yes('Enable deep-research?', ctx.get_config('deep_research_enabled', True))
        selected = (['crawl4ai'] if crawl == 1 else []) + (['searxng'] if search == 1 else [])
        print(f'Extraction: {crawl_url}; bearer token: {"configured (hidden)" if token else "none"}')
        print(f'Search: {search_url or "keep current provider"}; save_finding={save}; deep-research={research}')
        print('Set web.extract_backend=crawl4ai' + (' and web.search_backend=searxng' if search_url else ''))
        for service in selected:
            print(f'Deploy {service}: {managed_record(ctx, service)["directory"]}; loopback port {PORTS[service]}')
        print('Existing managed files/data are retained. Restart running Hermes sessions after setup.')
        if not yes('Apply these changes?', False):
            print('Cancelled; no changes applied.')
            return 0
        require_writable(search_url is not None, crawl == 1)
        for service in selected:
            record = managed_record(ctx, service)
            preflight_service(service, Path(record['directory']), record['project'], service in records)
        for service in selected:
            record = managed_record(ctx, service)
            if service == 'crawl4ai':
                save_provider_env_credential(MANAGED_TOKEN, token)
            try:
                provision_service(service, Path(record['directory']), record['project'], token=token if service == 'crawl4ai' else '')
            finally:
                # Record partial creation too, so a failed startup remains explicitly stoppable.
                if Path(record['directory']).exists():
                    records[service] = record
                    ctx.state.set('managed_services', records)
        for attempt in range(10 if selected else 1):
            try:
                check_services(crawl_url, token, search_url)
                break
            except RuntimeError:
                if not selected or attempt == 9:
                    raise
                time.sleep(3)
        save_provider_env_credential('CRAWL4AI_API_TOKEN', token)
        save_provider_env_credential('CRAWL4AI_URL', crawl_url)
        if search_url:
            save_provider_env_credential('SEARXNG_URL', search_url)
        ctx.set_config('crawl4ai_url', crawl_url)
        ctx.set_config('save_finding_enabled', save)
        ctx.set_config('deep_research_enabled', research)
        set_routing(search_url is not None)
        print('Setup verified. Restart running Hermes sessions to load the settings.')
        return 0
    except (EOFError, KeyboardInterrupt):
        print('\nSetup cancelled.')
        return 1
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        safe = str(exc) if isinstance(exc, (ValueError, RuntimeError)) else 'Configuration or command failed.'
        print(f'Setup failed: {safe}\nSome deployment/settings changes may have completed. Files are retained; rerun setup or use hermes crawl4searxng stop for owned services.')
        return 1


def run_stop(ctx):
    try:
        for record in ownership(ctx).values():
            stop_service(Path(record['directory']), record['project'])
        print('Owned services stopped; settings, credentials and volumes retained.')
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f'Stop failed: {exc}')
        return 1


def register_cli(ctx):
    def setup(parser):
        commands = parser.add_subparsers(dest='crawl4searxng_action', required=True)
        commands.add_parser('setup', help='Configure managed Docker or existing services')
        commands.add_parser('stop', help='Stop only owned services, retaining data')

    def handler(args):
        return run_setup(ctx) if args.crawl4searxng_action == 'setup' else run_stop(ctx)

    ctx.register_cli_command(name='crawl4searxng', help='Configure Crawl4AI/SearXNG', setup_fn=setup, handler_fn=handler)
