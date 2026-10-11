# Verification record

Implementation and verification started October 10 and continued October 11, 2026.

## Runtime and checks observed

- Main Hermes's authorized updater completed at `b65cd56cfcdc`, reporting
  `0.21.6+606.gb65cd56.dirty`, Python 3.14.7. The initial 0.16.0 banner was a stale
  release stamp before interrupted-update completion; it is not the final floor.
- `hermes --run-module unittest discover -s tests -v`: **24 tests passed**.
  Covers six wizard service combinations, default feature registration/opt-outs,
  no-terminal/EOF/declined confirmation, malformed endpoints/responses, scoped
  secret errors, token redaction, failed-probe routing preservation, administrator
  locks, occupied ports, symlinks, atomic UTF-8 notes, ownership, secret/custom
  settings preservation, stop retention, and legacy script refusals.
- `hermes plugins doctor --ci <implementation>`: passed real discovery,
  manifest parsing, import, and registration; one tool, zero hooks.
- `hermes plugins validate <clean-release-checkout> --install-deps`: passed manifest,
  configuration, load/capability checks, safe security scan, and no-core-override.
  A separate new temporary dependency environment failed on Matrix's python-olm
  build because clang++ was absent; using the installed Hermes runtime passed.
- Docker access works through a fresh `sg docker` session after the user joined
  that group. Existing containers occupy both default ports; they remain running.

## Release image pins

Official Docker Hub tag metadata supplied these multi-architecture digests:

| Image | Digest |
| --- | --- |
| unclecode/crawl4ai | sha256:9021b3cb5c6f12570bbcd5395638495e0a06969b3148e377b953d174af2ebc9b |
| searxng/searxng | sha256:85492ba800a861e3e8ff6014c430e81369fe6ca766a9990595f616d1ce95b272 |
| valkey/valkey | sha256:48332870af354a799964c0012ae1194a0bf2bf894eb508f945810596dc2d8d11 |

Live startup, authenticated probes, invalid-token rejection, repeat deployment,
and stop/volume-retention checks **passed** on Linux ARM64. `tests/live_docker.py` uses alternate loopback ports 31235/38080 so
existing services are not stopped. This tests the actual deployment code and
images; the six complete wizard combinations are covered by unit tests.

## Research evidence

The old skill ran through main Hermes with web tools and a three-call limit on
the self-hosted-token question. It answered the paid-key distinction correctly,
but used bare domain references rather than inline supporting-page links and
attempted a nonexistent guide path before exhausting its budget. No notes were
requested. The real configured-model fixture evaluation ran 20 valid conversations. The
tightened skill retained useful facts in 5/5 follow-ups; complete clickable
citations appeared in only 1/5. See `deep-research-evaluation.md` for raw counts,
failed candidates, and limitations. A final absence-claim wording adjustment was
not reevaluated. A live browsing smoke is separately recorded below.
See `research-baseline.md` for separately labeled simulated instruction analysis.

## Live installation and recovery

Native pinned local-Git install, terminal setup against both existing services,
normal native removal/reinstall, explicit skill registration, native search and
extraction, private-URL rejection, and native UTF-8 save_finding in a disposable
home **passed**. The initial malformed-URL test aborted in Hermes normalization;
the mixed-result case uses a well-formed private URL. A brittle example-page
heading assertion was replaced by nonempty successful extraction.

Live normal native removal/reinstall also passed. Hermes rejected removal of the
old external development symlink; only its verified link was explicitly removed,
and the repository was preserved. The main profile setup and final invariant
comparison are recorded in the release verification supplement.

Native loading revealed that runtime manifest capabilities is a list, distinct
from the catalog entry mapping. A failing regression reproduced the warning;
the inappropriate mapping was removed. Top-level tool declarations remain.
Clean-checkout catalog validation passed; a generated test-home scan was stopped
and excluded. Validate release trees without backups or generated runtime files.

A mode-0600, 261.9 MB protected backup contains 4,754 Hermes-home files, excluding
managed caches and source/runtime directories. Its mode-0700 parent is outside
the committed plugin tree (`.implementation/private/`). The older /tmp backup
did not survive the session interruption. Restore only affected plugin settings
and installation metadata if needed; do not overwrite concurrent user edits.

## Main-profile results

The live terminal wizard completed with existing Crawl4AI/SearXNG, retained bearer
credentials, both optional features enabled, and successful probes. Native web
wrappers and explicit plugin-skill registration passed in the main profile.
Research-note hashes and unrelated plugin-entry hashes were unchanged; extraction routing
remained Crawl4AI, and the confirmed wizard changed the blank search backend to
explicit SearXNG as selected. The original three containers
were left running. The compact plugin list differed only in this plugin's version and pinned SHA;
all other enabled/disabled statuses and versions were unchanged.

Full tested Hermes source revision:
`b65cd56cfcdc33cbf6657326b5711a7c23cd1485`.

## Live research smoke

`hermes --profile default chat --skills hermes-crawl4searxng:deep-research -t web
--max-turns 4 --run-budget 90 --oneshot -q <token-question>` exited successfully.
It fetched the official self-hosting page and distinguished a locally generated
bearer token from a purchased API key. The redacted native Markdown session
export confirms two actual adjacent Markdown links to the read documentation;
console rendering displayed only their labels. The broader cloud comparison and
Docker-command paragraph lack their own adjacent citation, so this single smoke
does not establish universal citation compliance. No knowledge notes were saved.
The export records two tool invocations; the CLI summary counts four tool-call
messages (calls plus results). Initialization precedes the agent's run budget.
An initial CLI invocation used obsolete one-shot syntax and exited before model
execution; it is excluded from the successful smoke.

The main profile has a preexisting malformed `skills.external_dirs` string that
Hermes warns about. Plugin-scoped skill registration/loading passed independently;
the unrelated setting was preserved.

## Release checks and limits

The project-tree suite passed all 24 tests; both shell scripts passed `bash -n`.
A clean checkout at the final catalog draft's full SHA is validated separately,
with its validator output retained in ignored `.implementation/.test-artifacts/`.
Generated catalog YAML is outside the committed tree so its pin is not circular.
No push or submission was performed. This commit must become public in the named
repository before the draft can be admitted.

Six wizard combinations are tested with deterministic unit fixtures. Real Docker
coverage tests managed deployment code on alternate ports; real native terminal
coverage tests existing/existing service setup. These are not six fully live
end-to-end deployments. Other operating systems/architectures were not exercised.
Real research quality remains model dependent; the repeated mini-model fixture
run failed consistent citation formatting despite the explicit instructions.
