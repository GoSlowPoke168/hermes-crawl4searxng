# Terminal Setup and Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Implement in this session; skill behavior evaluations may use isolated agents where required by the writing-skills workflow. Steps use checkbox syntax for tracking.

**Goal:** Deliver a terminal wizard with managed/external service choices, substantially improve evidence-based research, and verify the original plugin for Hermes catalog submission.

**Architecture:** Keep the existing provider, entrypoint, tool, and bundled skill. Add `cli.py` for terminal orchestration and `deployment.py` for managed Compose lifecycle; store settings, secrets, and ownership through Hermes' supported routes. Native installation remains separate from explicit provisioning.

**Tech Stack:** Python standard library, existing Hermes/httpx/YAML runtime, Docker Compose, Hermes public plugin APIs, Markdown skills. No GUI or new production dependency.

**Spec:** [2026-10-10-setup-and-catalog-design.md](../specs/2026-10-10-setup-and-catalog-design.md)

## Global constraints

- Preserve `hermes-crawl4searxng`, backend `crawl4ai`, and existing service env configuration.
- Release version: `1.1.0`; establish the Hermes SemVer floor through contract checks before finalizing metadata.
- Docker is the wizard's initial default, independently overridable per service. Both extras initially default to enabled.
- No deployment/prompting at import or registration; missing credentials must not hide setup.
- Secrets use Hermes routes; secret values never appear in command arguments, logs, plans, or committed fixtures.
- No purge, self-updating code, GUI, mandatory research delegation, or new paid provider.
- Preserve live data, credentials, profiles, existing plugin enablement, and unrelated settings. Use an isolated implementation checkout because the live plugin points to this repository.
- User authorization covers main Hermes upgrade and this plugin's remove/reinstall test. Filesystem/network escalation may still be required by the execution environment.

## Review focus

1. A missing token in one profile must not use another profile's credential (Task 2).
2. Missing initial configuration must not prevent CLI discovery (Tasks 1–2).
3. Cancelled setup or failed Docker launch must not overwrite working routing or claim ownership of an external service (Tasks 3–4).
4. Existing secrets/settings and occupied legacy ports must survive repeated setup and cleanup (Tasks 3, 5, 7).
5. An extracted page with malicious instructions or conflicting claims must produce grounded research without unauthorized actions (Task 6).

## Task 1: Establish contracts and upgrade Hermes with rollback

**Files:** Create `docs/testing/2026-10-10-verification.md`; no product code yet.

**Interfaces:** Establish the exact credential writer and CLI/settings/skill contracts used by subsequent tasks; record the Hermes interpreter, checkout SHA, version, supported validation command, and compatible minimum release.

- [ ] Recheck main Hermes checkout status, active profiles, services, and `hermes update --plan`; record metadata without credentials. The observed baseline checkout is clean, but rerun before writing.
- [ ] Make a protected backup of plugin installation identity, relevant profile settings/credentials, notes, deployment paths, and Hermes revision using Hermes backup facilities. Record a targeted restore procedure; do not commit the backup.
- [ ] Run the authorized normal Hermes upgrade with backups enabled, preserving local changes and profiles. Do not use force options or skip backup. Check `hermes --version`, core diagnostics, and unrelated enabled plugin identities afterward.
- [ ] In a temporary Hermes profile, exercise a throwaway plugin registering `crawl4searxng setup` with no service env set. Check native discovery and `--help` do not mutate config or start Docker.
- [ ] Verify a public credential write route in the upgraded runtime, including managed-profile refusal and redaction. Do not assume that the installed `save_env_value_secure` helper is an approved plugin API. If no supported route exists, report the missing surface before coding a private workaround.
- [ ] Confirm the active profile/home API, namespaced skill loading, CLI registration with no required env gate, and current native extract response contract using the real runtime.
- [ ] Establish a temporary implementation checkout using the worktree skill; never attach unfinished code to the live plugin symlink. Use the supported Hermes interpreter for tests; the pre-upgrade launcher uses `/home/akari/.hermes/hermes-agent/venv/bin/python`, but rediscover after upgrade.
- [ ] Run `hermes plugins validate /home/akari/Projects/hermes-crawl4searxng --install-deps` if available; otherwise inspect the actual canonical validator and report the docs/runtime mismatch. Record failures to fix in later tasks, without calling old `doctor` equivalent to catalog CI.

## Task 2: Configuration, scoped credentials, and conditional registration

**Files:** Modify `plugin.yaml`, `__init__.py`, `provider.py`; create `tests/test_plugin.py`, `tests/test_provider.py`.

**Interfaces:** `register(ctx) -> None` remains the entrypoint. Extend `Crawl4AIWebSearchProvider` to consume a settings getter while preserving standalone construction. Keep `extract(urls, **kwargs)` aligned with the runtime contract established in Task 1. `save_handler(args, **kwargs) -> str` stays compatible.

- [ ] Write failing tests `test_register_without_service_credentials`, `test_default_extras_enabled`, `test_extras_independently_disabled`, `test_secret_scope_miss_has_no_global_fallback`, and `test_save_uses_active_hermes_home`. Assert no deployment or network calls during registration/availability checks.
- [ ] Add provider cases for missing URL, valid markdown, HTTP 401/500, connection timeout, invalid JSON, non-object JSON, unsuccessful response, invalid markdown type, and mixed URL successes/failures. Assert individual failures retain URL identity and do not abort subsequent URLs.
- [ ] Run the new tests with `python -m unittest discover -s tests -v` under the verified Hermes runtime; confirm failures reflect missing behavior rather than broken imports.
- [ ] Declare the specified schema, remove credential load gating, and pass configuration access through the existing provider. Use scoped secret reads without broad fallback; retain supported env compatibility.
- [ ] Conditionally register the tool and namespaced skill using plugin settings. Preserve default behavior; resolve note writes to active Hermes home and use explicit UTF-8.
- [ ] Run tests and real Hermes discovery under configured and unconfigured temporary profiles. Assert secret sent in the request is the selected profile's token and never appears in errors.
- [ ] Review and commit this independently testable change in the implementation checkout.

## Task 3: Managed deployment with explicit ownership

**Files:** Create `deployment.py`, `tests/test_deployment.py`; modify both Compose files and the SearXNG settings template only as needed.

**Interfaces:** `provision_service(service: str, directory: Path, project_name: str, *, token: str = "") -> None` provisions one selected service; `stop_service(directory: Path, project_name: str) -> None` retains data. Service is restricted to `crawl4ai` or `searxng`. Exceptions are handled by the CLI. Ownership is stored by the orchestrator in Task 4, rather than inferred from directory existence.

- [ ] Write failing tests `test_token_and_settings_survive_rerun`, `test_external_service_never_provisioned`, `test_compose_argv_handles_space_in_directory`, `test_legacy_container_collision_is_not_adopted`, `test_failure_reports_service_without_secret`, and `test_unowned_directory_is_never_stopped`.
- [ ] Run deployment tests and confirm expected failures.
- [ ] Reuse templates under `plugin-data/hermes-crawl4searxng/deployment/`. Generate missing secrets with standard-library `secrets`; persist secure files with mode 0600. Never read Hermes credential files directly.
- [ ] Remove fixed global container names for new deployments; derive stable per-profile project identity from deployment location. Preserve loopback port binding and detect collisions before deployment; do not silently migrate old containers.
- [ ] Use bounded argument-list subprocess calls with explicit Compose files/project names. Reject symlinked secret/config destinations that could overwrite files outside managed data.
- [ ] Inspect official image releases, select tested immutable digests, and resolve both Compose files with temporary fixture env. Do not print rendered configs containing real credentials.
- [ ] Run unit tests and isolated real Compose startup/stop tests. Verify the existing files survive rerun and stop; remove only test-created containers/resources after testing.
- [ ] Review and commit.

## Task 4: Terminal setup, service checks, and configuration application

**Files:** Create `cli.py`, `tests/test_cli.py`; modify `__init__.py` for CLI registration.

**Interfaces:** `register_cli(ctx) -> None` registers top-level `crawl4searxng` with `setup` and `stop`. `run_setup(ctx) -> int` collects selections and applies them after confirmation. `check_services(crawl4ai_url: str, token: str, searxng_url: str | None) -> None` runs bounded service probes. `run_stop(ctx) -> int` consumes only recorded ownership. The CLI uses Task 3's deployment functions.

- [ ] Write failing tests for managed/managed, external/external, managed/external, external/managed, and keep-current-search selections. Assert both extras default true and each can be disabled independently.
- [ ] Add `test_no_tty_exits_without_changes`, `test_eof_cancels_collection`, `test_declined_summary_has_no_changes`, `test_bad_url_is_reprompted`, `test_blank_token_reports_auth_failure`, `test_secret_is_hidden`, `test_managed_profile_refuses_write`, and `test_failed_probe_does_not_change_working_routes`.
- [ ] Run CLI tests and confirm expected failures.
- [ ] Implement collection with standard-library prompts/getpass; reuse prior values. Validate HTTP(S) endpoints and reject embedded credentials. Show an accurate redacted summary, then request confirmation.
- [ ] Preflight dependencies/ports/config writability, deploy only selected services, and record successful managed creations before probes. Preserve recovery metadata if probes fail; do not automatically delete failed deployments.
- [ ] Probe `POST /md` with the token and a stable public URL; check success and nonempty string markdown. Probe SearXNG `/search` with JSON format and validate the result shape; an empty result list is not inherently a service failure.
- [ ] After probes pass, persist settings/credentials through the verified Hermes routes and apply explicit extraction/search routing. Keep-current-search leaves its env/routing untouched. Report partial persistence errors clearly rather than claiming transactional success.
- [ ] Run tests and actual PTY wizard sessions in a temporary Hermes home. Bound prompts/subprocesses and check error exits. Check output and tool traces for secret leakage.
- [ ] Review and commit.

## Task 5: Cleanup, legacy migration, and repeatability

**Files:** Modify `install.sh`, `uninstall.sh`, `README.md`; extend `tests/test_cli.py`, `tests/test_deployment.py`.

**Interfaces:** Shell scripts are compatibility entrypoints only. `stop` requires recorded directories/project identities; native Hermes manages plugin installation/removal.

- [ ] Write failing tests asserting stop preserves data, no ownership means no Docker command, externally selected legacy services are untouched, and purge/old location flags return actionable migration messages.
- [ ] Replace code-copy/deployment logic in `install.sh` with the installed setup entrypoint; when absent, print native install/enable instructions. Reject obsolete mode flags explicitly. Make `uninstall.sh` direct users through managed stop/native removal and refuse purge.
- [ ] Document migration from both legacy locations and existing fixed-name containers: select their endpoints as external services, keep existing files/secrets, and avoid automatic adoption/recreation. Document managed stop before plugin removal and persistence after removal.
- [ ] Run `bash -n install.sh uninstall.sh`, shell help/error checks, ownership tests, and repeated wizard sessions. Verify no installed code files change as a result of setup.
- [ ] Review and commit.

## Task 6: Rewrite and behavior-test deep-research

**Files:** Modify `skills/deep-research/SKILL.md`; create `tests/fixtures/research-cases.md`, `docs/testing/deep-research-evaluation.md`; update README usage.

**Interfaces:** Keep skill name `deep-research`, invoked as `hermes-crawl4searxng:deep-research`. Consume only native `web_search`/`web_extract` plus optional `save_finding`. No new production script or research provider.

- [ ] Create six scenarios: current software comparison, conflicting reports, inaccessible primary page with misleading snippet, syndicated copies of one source, injected instructions in extracted content, and save-request versus no-save-request. Use deterministic source/tool fixtures for adversarial cases, plus real public sources for live tests.
- [ ] Before rewriting, run representative scenarios against the old skill in isolated Hermes sessions; preserve redacted output/tool traces and score claim support, primary-source use, conflict treatment, inline citation validity, stopping behavior, and unauthorized persistence.
- [ ] Review the online reference skill and its MIT license at a fixed commit. Prefer an original Hermes-specific rewrite; retain required notices for any reused text. Do not inherit Claude-specific model/tool/delegation assumptions.
- [ ] Write the scope/search/evidence/verification/synthesis workflow from the spec. Include one compact report example, extraction-failure handling, confidence tied to evidence, prompt-injection boundaries, and optional saving. Keep instructions usable rather than adding a large research framework.
- [ ] Repeat fixtures and live Hermes runs with the revised skill. Reopen cited URLs and manually check material claims; do not grade correctness solely by an LLM or by number of citations. For behavioral wording changes, use repeated fresh-context samples and no-guidance controls as required by writing-skills.
- [ ] Require all injected-action/save-permission checks to pass and demonstrate improvement over baseline for source support/conflict handling. Fix failures and rerun affected scenarios. Record model, dates, fixture versions, limitations, and observed usage.
- [ ] Confirm actual namespaced skill resolution and README's invocation instructions; no automatic-activation claim unless verified through a public Hermes surface.
- [ ] Review and commit.

## Task 7: Real Hermes install/remove/reinstall and full verification

**Files:** Extend `docs/testing/2026-10-10-verification.md`; add `tests/test_hermes_integration.py` for isolated runtime checks where useful.

**Interfaces:** Use native plugin management and real `web_search`/`web_extract` wrappers, not just direct calls to the provider.

- [ ] Run the full unit suite once all implementation tasks pass, followed by shell checks, real plugin validation, and isolated registration/wizard tests.
- [ ] In temporary profiles test fresh installation without credentials, each managed/external/mixed selection, keep-current search, repeat setup, invalid token, unreachable service, and namespaced skill loading. Validate loopback exposure and ownership-based stop.
- [ ] Invoke real Hermes native search/extract against the selected services, including a mixed successful/failed URL extraction request. Save a test finding only inside a temporary profile; verify UTF-8 content and citations there.
- [ ] Before touching the live plugin, take a protected metadata/config backup, recheck services/profiles and local edits, and verify native removal handles a symlink without deleting its repository target. Test symlink removal semantics on a temporary installation first.
- [ ] Perform the authorized live remove/reinstall using native Hermes management and the locally reviewed implementation revision. If the native installer cannot install a local git source, deploy a reviewed plugin copy explicitly for this test; reserve remote SHA installation for the published release. Do not push solely to make a test possible.
- [ ] Configure the live setup using existing services first, preserving their credentials/data/custom settings. Confirm real extraction/search and skill loading; run research smoke tests without saving actual user notes.
- [ ] Compare unrelated enabled plugins/settings and service state with baseline. If the live test fails, restore the prior plugin installation and only its changed settings; keep diagnostic artifacts redacted. Never wholesale-restore over concurrent user edits.
- [ ] Leave the working verified plugin enabled, with a clear record of installation location and managed services; do not leave live Hermes attached to an abandoned temporary worktree.
- [ ] Record exact commands, exit codes, runtime SHA/version, tested image digests, passed paths, remaining limitations, and the restore procedure. Do not claim exhaustive compatibility beyond this matrix.

## Task 8: Release metadata and reviewable catalog submission

**Files:** Modify `plugin.yaml`, `README.md`, `.gitignore`; create `docs/catalog-submission.md`; create the catalog entry in a separate Hermes checkout only after the release commit is available.

**Interfaces:** Version `1.1.0`; original repo `https://github.com/GoSlowPoke168/hermes-crawl4searxng`; one catalog entry pinned to the actual full release commit SHA.

- [ ] Add matching capability/environment declarations and truthful minimum Hermes version based on Task 1. Confirm optional registration settings are compatible with the validator's capability comparison.
- [ ] Document network behavior, local Docker/background processes, secret storage, notes outside installed code, same-topic note replacement, explicit setup confirmation, external-service behavior, host/container limitations, migration, and native catalog updates. Ignore generated secret/config artifacts if any tooling can create them under the repository.
- [ ] Check install/update scripts cannot fetch or replace reviewed plugin code outside Hermes' native lifecycle. Inspect security scan results and resolve dangerous findings; explain any remaining caution finding rather than bypassing validation.
- [ ] Run `hermes plugins validate <clean-release-checkout> --install-deps` using current catalog Hermes and its canonical CI check; capture the actual SHA and quoted version. If runtime docs disagree with canonical validation, resolve the discrepancy before claiming readiness.
- [ ] Draft the exact catalog entry and PR description against the current entry schema, including required disclosures. Revalidate the exact pinned tree, not merely the dirty development checkout.
- [ ] Deliver code diff, test evidence, upgrade/reinstall outcome, and catalog draft for review. Push/publication/submission remain separate actions after the user reviews the finished result.

## Completion criteria

All automated checks pass; all wizard paths and native installation lifecycle are exercised with real Hermes; the main Hermes upgrade and live plugin reinstall succeed without lost user data or unrelated settings; revised research behavior meets its evidence rubric; current catalog validation succeeds against the exact proposed release commit. Any inaccessible network/service or validator discrepancy is reported as an outstanding check, not recorded as a pass.

## Plan self-review

The tasks cover each design section and all five review-focus cases. Runtime-contract checks precede decisions that depend on them, deployment ownership is recorded before health verification, setup does not gate CLI availability on credentials, and catalog submission is separated from live installation testing. The final Hermes floor and image digests are measured outputs of named verification steps, not guessed literals.
