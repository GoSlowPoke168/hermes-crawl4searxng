"""Explicitly owned Compose deployments; credentials/config survive stop and reruns."""
import hashlib
import os
import secrets
import shutil
import socket
import subprocess
from pathlib import Path

PORTS = {'crawl4ai': 11235, 'searxng': 8080}
TEMPLATES = Path(__file__).parent / 'docker'


def project_name(directory):
    return 'hermes-c4s-' + hashlib.sha256(str(directory.resolve()).encode()).hexdigest()[:12]


def check_directory(directory):
    if any(part.is_symlink() for part in (directory, *directory.parents)):
        raise ValueError('Managed-service directory cannot be a symlink')


def compose(directory, project, *arguments):
    try:
        return subprocess.run(['docker', 'compose', '--project-name', project, '--file', str(directory / 'docker-compose.yml'), *arguments], cwd=directory, capture_output=True, text=True, check=True, timeout=300)
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError('Docker Compose failed; inspect this managed project locally (output may contain secrets).') from None


def preflight_service(service, directory, project, owned):
    check_directory(directory)
    if directory.exists() and not owned:
        raise ValueError('Managed-service directory already exists without recorded ownership')
    try:
        subprocess.run(['docker', 'compose', 'version'], capture_output=True, check=True, timeout=15)
        subprocess.run(['docker', 'info'], capture_output=True, check=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        raise RuntimeError('Docker daemon/Compose is unavailable. Check Docker permissions or select an existing service.') from None
    if owned and (directory / 'docker-compose.yml').is_file():
        if compose(directory, project, 'ps', '--status', 'running', '-q').stdout.strip():
            return
    with socket.socket() as listener:
        try:
            listener.bind(('127.0.0.1', PORTS[service]))
        except OSError:
            raise RuntimeError(f'Port {PORTS[service]} is occupied. Select that service as an existing instance; it will not be adopted.') from None


def write_new(path, content):
    if path.is_symlink():
        raise ValueError('Managed-service file cannot be a symlink')
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        stream.write(content)


def provision_service(service, directory, project, *, token=''):
    if service not in PORTS:
        raise ValueError('Unknown managed service')
    if service == 'crawl4ai' and (not token or any(char in token for char in '\r\n\x00')):
        raise ValueError('Crawl4AI token must be nonempty and single-line')
    check_directory(directory)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    compose_file = directory / 'docker-compose.yml'
    write_new(compose_file, (TEMPLATES / service / 'docker-compose.yml').read_text())
    if service == 'crawl4ai':
        escaped = token.replace('\\', '\\\\').replace("'", "\\'")
        write_new(directory / '.env', f"CRAWL4AI_API_TOKEN='{escaped}'\nSECRET_KEY={secrets.token_hex(32)}\n")
    else:
        config = directory / 'core-config'
        check_directory(config)
        config.mkdir(exist_ok=True)
        template = (TEMPLATES / service / 'core-config/settings.yml.template').read_text()
        write_new(config / 'settings.yml', template.replace('__GENERATED_SECRET_KEY__', secrets.token_hex(32)))
        write_new(directory / '.env', 'SEARXNG_HOST=127.0.0.1\nSEARXNG_PORT=8080\n')
    compose(directory, project, 'up', '-d')


def stop_service(directory, project):
    check_directory(directory)
    compose(directory, project, 'down')
