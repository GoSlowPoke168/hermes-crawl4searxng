# Latest-image setup verification

Release 1.1.1 makes managed setup pull the configured images before startup.
Crawl4AI and SearXNG default to `latest`; Valkey retains its existing digest.
The former plugin-default Crawl4AI/SearXNG pins migrate on setup. Custom image
choices, Compose comments/ports, credentials, and SearXNG settings are retained.
Updates run only after setup confirmation; no background updater is added.

- **32 unit tests passed** through the installed Hermes runtime. New coverage
  includes fresh/repeated pulls, old-pin migration, custom pins, pull failures
  preventing startup, and atomic migration failure preserving the original file.
- **Live Docker checks passed on Linux ARM64**, on alternate ports 31235/38080:
  fresh startup, authenticated markdown extraction, SearXNG JSON search,
  invalid-token rejection, old-pin migration, repeat setup, retained credentials,
  and stop retaining volumes. Only test projects and their test volumes were removed.
- **Hermes plugin validation passed** on a clean tracked-file copy, including
  registration, capability checks, safe security scan, and no core override.
- Shell syntax and `git diff --check` passed.

Other operating systems/architectures remain untested live. These results cover
images available during this run; future upstream `latest` images are not verified.
The user's existing default-port containers were not updated by these tests.
