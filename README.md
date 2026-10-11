# hermes-crawl4searxng

Crawl4AI extraction for Hermes's native `web_extract`, paired with Hermes's
built-in SearXNG `web_search`. Use your own services or let a terminal wizard
deploy Docker. Includes an optional cited-note tool and deep-research skill.

## Install and configure

Requires Hermes **0.21.6 or newer**. Tested on Linux ARM64; managed deployment
requires a host-installed Hermes CLI, Docker daemon access, and Docker Compose.

```bash
hermes plugins install GoSlowPoke168/hermes-crawl4searxng --enable
hermes crawl4searxng setup
```

The owner/repository shorthand works before catalog listing. Once admitted to
the official catalog, install with `hermes plugins install hermes-crawl4searxng
--enable` to get the reviewed SHA. Installation enables the plugin; **run setup
separately**. Installing or loading it never prompts or starts containers.

The wizard offers these choices independently:

| Service | Initial default | Other choices |
| --- | --- | --- |
| Crawl4AI | Deploy Docker | Existing HTTP(S) endpoint and hidden bearer token |
| Search | Deploy SearXNG Docker | Existing SearXNG endpoint; keep current search |
| save_finding | Enabled | Disable |
| deep-research | Enabled | Disable |

It reuses existing configured endpoints on later runs, shows the proposed URLs,
deployment directories, and routing changes, then asks for confirmation. It checks
authenticated extraction and SearXNG JSON search before changing working routes.
Restart existing Hermes sessions after setup. Interrupted or failed deployment
retains its files and ownership record; inspect it, rerun setup, or stop it.
Configuration writes are sequential: an error during persistence can leave some
settings applied, and setup reports that possibility.

For existing Crawl4AI, a blank token keeps the configured value; enter `-` for an
instance that needs no token. There is **no purchased Crawl4AI key requirement**.
Current self-hosted Docker images require local bearer authentication to expose
their server outside the container. Managed setup generates a local token when
none is configured. Optional LLM extraction/cloud services have separate keys;
this plugin's `/md` extraction does not require those services. See the
[official self-hosting guide](https://docs.crawl4ai.com/core/self-hosting/).

Managed services bind `127.0.0.1:11235` and `127.0.0.1:8080`, use pinned immutable
images, and have a separate Compose project per profile/deployment. An occupied
port causes an actionable error; existing containers are never adopted silently.
The wizard requires a terminal and refuses unattended invocation without changes.
When Hermes itself runs in Docker, select existing service URLs reachable from
its container (such as your Docker network's service names).

Hermes profiles configured with `plugins.isolation: host` skip plugin CLI
registrations: the provider/tool can load, but this terminal command needs the
normal `in_process` mode. The plugin does not change that policy automatically.

## Existing configuration and optional features

Existing `CRAWL4AI_URL`, `CRAWL4AI_API_TOKEN`, and `SEARXNG_URL` remain supported.
The token is read through Hermes's profile-scoped secret API. Secrets are saved
through Hermes's credential route, never written into plugin settings YAML.

```yaml
plugins:
  entries:
    hermes-crawl4searxng:
      enabled: true
      settings:
        crawl4ai_url: http://127.0.0.1:11235
        save_finding_enabled: true
        deep_research_enabled: true
web:
  extract_backend: crawl4ai
  search_backend: searxng
```

The URL setting takes precedence over the legacy environment value. Keeping the
current search provider in setup leaves its endpoint/routing untouched. Without
an extraction endpoint, the plugin still loads and setup remains available.

Load the research skill explicitly:

```bash
hermes --skills hermes-crawl4searxng:deep-research -z 'Research my question with verified inline citations'
```

It directs Hermes to read sources, prioritize primary evidence, distinguish
versions/dates, investigate conflicts, recognize copied reporting, reject page
instructions, and disclose unresolved gaps. Skill registration does not promise
automatic activation. `save_finding` is used only when requested and available.
Notes are UTF-8 Markdown in the active Hermes home's `knowledge/` directory.
**Saving the same normalized topic replaces its prior note.** Replacement is
atomic, so a failed write leaves the prior note intact.

## Stop, remove, and migrate

```bash
hermes crawl4searxng stop
hermes plugins remove hermes-crawl4searxng
```

Stop affects only projects recorded by this plugin in the active profile. It
retains volumes, generated settings, and credentials. Native plugin removal does
not stop services or delete research notes. There is no purge command.

Generated deployment files live under `ctx.state.data_dir/deployment/`, within
the active Hermes home's `plugin-data/` namespace, outside installed code. The
wizard never overwrites existing generated secrets or custom SearXNG settings.
An existing managed Compose file also remains unchanged on rerun; adopting a
new image digest for that deployment is an explicit administrator edit.

If you used the old scripts or fixed container names (`crawl4ai`, `searxng-core`,
`searxng-valkey`), keep those containers/files and select their endpoints as
**existing instances**. Remove obsolete bundled/code-copy installations through
their original lifecycle after confirming the native plugin works; do not leave
duplicate providers enabled. `install.sh` now forwards to setup; legacy
`--bundled`, `--standalone`, and `--symlink` options fail with migration guidance.
`uninstall.sh` prints native stop/remove instructions and refuses `--purge`.

## Behavior and disclosures

- Extraction sends the requested page URL and bearer token to your configured
  Crawl4AI server; that server fetches/renders the page. Search queries go to
  SearXNG and its configured search engines. Setup probes `https://example.com`
  and searches for `Hermes Agent` to verify both services.
- Confirmed managed setup runs bounded `docker`/`docker compose` commands, pulls
  the pinned images if missing, and starts background containers with restart
  policies. It uses no shell interpolation of entered values.
- Hermes stores profile credentials through its credential lifecycle API.
  Managed Crawl4AI additionally needs its own mode-0600 deployment `.env` file;
  this is a generated service file, not a read of Hermes's credential store.
  Its token is also retained through Hermes as `CRAWL4AI_MANAGED_API_TOKEN`, so
  switching to an external instance and back preserves authentication. If that
  credential is lost, setup asks for the existing managed token rather than
  replacing the service's secret file.
- Research notes and service data survive native updates/removal. Setup/stop
  do not touch externally managed containers. No telemetry is added.
- Plugin code updates use Hermes's native install/update lifecycle; there is no
  code copier or self-updater. Catalog updates require a reviewed SHA bump.

## Verification and catalog submission

```bash
hermes --run-module unittest discover -s tests -v
bash -n install.sh uninstall.sh
hermes plugins validate . --install-deps
```

See [verification evidence](docs/testing/2026-10-10-verification.md),
[research evaluation](docs/testing/deep-research-evaluation.md), and the
[catalog submission draft](docs/catalog-submission.md). Publication is a separate
reviewed step; local validation does not make the repository a catalog entry.
