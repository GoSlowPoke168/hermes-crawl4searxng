# Setup implementation ledger

The approved design and plan are in `docs/superpowers/`. Detailed evidence,
commands and limitations are in `2026-10-10-verification.md` and
`deep-research-evaluation.md`.

- Hermes upgraded to 0.21.6+606.gb65cd56.dirty, Python 3.14.7. Public API floor
  checked against v0.21.6. Protected backup and before/after hashes retained.
- 24 regression tests passed. Docker image startup, authenticated extraction,
  search JSON, invalid-token rejection, repeat deployment and stop/retention passed.
- Native installation/removal/reinstallation, disposable and main terminal setup,
  web wrappers, explicit skill discovery, and disposable UTF-8 note passed.
  Main notes and unrelated plugin entries/statuses unchanged; selected SearXNG
  routing explicitly set. Existing containers remain running.
- Fresh review found two Important defects, no Critical issues or declined
  judgments: explicit-profile routing and managed/external token transitions.
  Both fixed with observed failing-then-passing regression tests. Native smoke
  also exposed catalog/runtime capability-shape confusion; fixed and tested.
- 20 valid configured-model fixture conversations documented. Tightened useful
  fact retention 5/5; complete Markdown citations 1/5. Live browsing produced
  correct authentication advice and two verified inline links; this does not
  establish consistent citation quality. Final absence-claim wording unevaluated.
- Catalog draft is a separate review artifact. No push/publication/submission.

## Rulings and costs

- Use an ignored project-local clone for isolation: the native worktree is outside
  writable roots and /tmp work was lost between turns. Cost: extra local disk.
- Record partial managed creation before health checks so failed startup remains
  stoppable. Cost: a failed deployment may require explicit stop.
- Remove only the verified old development symlink before native install: Hermes
  rejects its outside-directory target. Cost: manual unlink; source preserved.
- Copy reviewed tracked files into a project feature branch, retaining untracked
  planning documents. Cost: consolidated project commit rather than clone history.
- Validate clean release checkouts: generated test runtimes otherwise enter the
  scanner. Cost: an additional local checkout; no scan rule is bypassed.
