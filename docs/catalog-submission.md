# Catalog submission draft

The implementation is published on the original repository; catalog submission
remains pending. Submit to the original GoSlowPoke168 repository lineage, whose
owner/maintainer authorized these changes.

The submission must pin a public full 40-character release commit. Generate
the catalog YAML from that exact commit after local tests and review, then run:

```bash
hermes plugins validate /path/to/clean-release-checkout --install-deps
```

Add `plugin-catalog/hermes-crawl4searxng.yaml` to NousResearch/hermes-agent with
name, public repository, full SHA, quoted version `"1.1.1"`, maintainer
`GoSlowPoke168`, tier `community`, category `web`, and floor `">=0.21.6"`.
Declare `provides_tools: [save_finding]`, no hooks/middleware, and no required
environment gating. URLs and bearer authentication are optional configuration;
unconfigured installs must expose setup. The final generated entry is a review
artifact outside the release tree to avoid a self-referential commit pin.

## Proposed PR description

This plugin supplies Crawl4AI extraction through Hermes's WebSearchProvider API
and pairs with Hermes's built-in SearXNG search. A separately invoked terminal
wizard connects existing services or deploys the latest Crawl4AI and SearXNG
Docker images, verifies the services, and configures routing. Rerunning managed
setup pulls before startup; custom image pins and service settings are preserved.
It defaults to optional save_finding and an explicitly loaded deep-research skill,
with independent opt-outs.

Public surfaces: register_web_search_provider, register_tool, register_skill,
register_cli_command, ctx.get_config/set_config/state, scoped get_secret, Hermes
credential lifecycle, and the native configuration CLI. No core functions or
private credential stores are patched/read. No Python dependency is added.

Disclosures: extraction sends requested URLs to the configured crawler, which
fetches/renders websites; SearXNG queries reach configured search engines. Setup
probes example.com and performs a test search. Confirmed managed setup executes
Docker/Compose, pulls the configured images before startup (latest Crawl4AI and
SearXNG by default; Valkey remains pinned), and starts background containers on
loopback. Hermes stores credentials through its credential route; generated
managed-service secret files additionally use mode 0600. Optional requested notes
write outside installed code to the active Hermes knowledge directory and replace
same-topic notes atomically. Data and credentials survive removal; external
containers are never stopped by the plugin. No telemetry or self-updater exists.

Compatibility: host-installed terminal setup, external endpoints when Hermes is
containerized. `plugins.isolation: host` skips CLI registration; the plugin does
not change isolation policy. Managed default ports must be free; legacy services
can be connected as existing endpoints. Updates require a reviewed catalog SHA
bump and native Hermes update.

Validation evidence is in docs/testing/2026-10-10-verification.md. The exact
full-SHA YAML is generated in the ignored .catalog-draft directory after the
release commit. Catalog submission and review remain separate from publishing
repository changes.
The configured mini-model citation reliability limitation is documented in
docs/testing/deep-research-evaluation.md; no model-independent quality claim is made.
Follow the [current admission rules](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins/catalog-submission).
