"""Opt-in real Compose test on alternate ports; never stops existing services."""
import importlib
import secrets
import shutil
import subprocess
import time
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import test_plugin

deployment = importlib.import_module('tested_plugin.deployment')
cli = importlib.import_module('tested_plugin.cli')
artifacts = test_plugin.ROOT / '.test-artifacts'
artifacts.mkdir(parents=True, exist_ok=True, mode=0o700)
root = Path(tempfile.mkdtemp(prefix='docker-', dir=artifacts))
templates = root / 'templates'
shutil.copytree(test_plugin.ROOT / 'docker', templates, dirs_exist_ok=True)
for service, old, new in [('crawl4ai', '11235:11235', '31235:11235'), ('searxng', '8080:8080', '38080:8080')]:
    file = templates / service / 'docker-compose.yml'
    file.write_text(file.read_text().replace(old, new))
token = secrets.token_hex(32)
created = []
try:
    with patch.object(deployment, 'TEMPLATES', templates), patch.dict(deployment.PORTS, {'crawl4ai': 31235, 'searxng': 38080}):
        for service in ('crawl4ai', 'searxng'):
            directory = root / 'deployment' / service
            project = deployment.project_name(directory)
            deployment.preflight_service(service, directory, project, False)
            created.append((directory, project))
            deployment.provision_service(service, directory, project, token=token if service == 'crawl4ai' else '')
            print(f'{service}: started on isolated loopback port', flush=True)
        for attempt in range(20):
            try:
                cli.check_services('http://127.0.0.1:31235', token, 'http://127.0.0.1:38080')
                break
            except RuntimeError:
                if attempt == 19:
                    raise
                time.sleep(3)
        print('Authenticated /md and SearXNG JSON probes passed', flush=True)
        try:
            cli.check_services('http://127.0.0.1:31235', 'invalid-fixture-token', None)
        except RuntimeError as exc:
            assert '401' in str(exc) or '403' in str(exc), str(exc)
        else:
            raise AssertionError('Invalid token was accepted')
        for directory, project in created:
            before = (directory / '.env').read_bytes()
            compose_file = directory / 'docker-compose.yml'
            latest, old = (
                ('unclecode/crawl4ai:latest', 'unclecode/crawl4ai@sha256:9021b3cb5c6f12570bbcd5395638495e0a06969b3148e377b953d174af2ebc9b')
                if directory.name == 'crawl4ai' else
                ('docker.io/searxng/searxng:latest', 'docker.io/searxng/searxng@sha256:85492ba800a861e3e8ff6014c430e81369fe6ca766a9990595f616d1ce95b272')
            )
            compose_file.write_text(compose_file.read_text().replace(latest, old))
            deployment.provision_service(directory.name, directory, project, token=token if directory.name == 'crawl4ai' else '')
            assert (directory / '.env').read_bytes() == before
            assert latest in compose_file.read_text()
            assert old not in compose_file.read_text()
        print('Invalid-token rejection, old-pin migration, and repeat deployment passed', flush=True)
finally:
    for directory, project in reversed(created):
        deployment.stop_service(directory, project)
        assert (directory / '.env').exists()
        volumes = subprocess.run(['docker', 'volume', 'ls', '--filter', 'label=com.docker.compose.project=' + project, '--format', '{{.Name}}'], check=True, capture_output=True, text=True).stdout.splitlines()
        if directory.name == 'searxng':
            assert len(volumes) == 2, 'stop removed test volumes'
        for volume in volumes:
            subprocess.run(['docker', 'volume', 'rm', volume], check=True, capture_output=True)
    print('Stopped only test projects; retention verified; test volumes cleaned', flush=True)
