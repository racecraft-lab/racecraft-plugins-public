# PR 1370: harm-halt repair

The main merge retains both `may_end` and `publication_pending`, plus every
pre-existing test from either parent. Generated payloads and references were
regenerated from the merged sources.

The repair closes the two findings on the previous reviewed head:

- `R1370-5cb5aeb8`: runner entry checks the standing halt before gates dispatch,
  including `payload-gate` / `payload-completeness` / `apply` with `apply_dist`.
- `R1370-34b45e54`: sweep isolation failure persists the harm halt before
  returning. Recoverable GitHub observation failures remain recoverable.

The follow-up spec note about printing the record is addressed in the shared
phase reference: read the existing `harm-halt` helper in `read_only` mode and
print its reason, redacted evidence, and last safe state before the stop marker.

## Known limits

- The standards re-review noted that `SchemaViolation` has no `reason`, so an
  invalid sweep request can also take the isolation fallback and persist a
  halt. Examples are an unknown capture surface or an unsupported receipt
  stage. This is a conservative refusal, with explicit human clearance; it
  neither bypasses the halt nor loses evidence. The supported orchestrator
  sends exact closed request shapes; reviewer prose cannot select these
  trusted request fields. A malformed direct caller can reach this limit.
  The earlier guidance already classified this fallback as the isolation halt.
  Separating invalid caller requests from invalid worker evidence would change
  that existing classification contract, so this repair retains it.
- The architecture advisory flags `gates/payloads.py` importing `runtime.py`.
  This edge exists unchanged on main. No architecture baseline or quality
  acknowledgment was changed to suppress it.
- Linux VM coverage excludes the two real macOS sandbox tests named in the PR
  verification reply. The orchestrator owns those tests and macOS plugin CI.
- The halt check and the payload gate find the repository root in different
  ways. `apply_refusal` uses `trusted_io.find_repo_root`, which stops at the
  nearest `.specify/`. `gates/payloads.py` uses `path_utils.find_repo_root`,
  which needs `tests/speckit-pro/`. A `payload-completeness` apply request with
  `apply_dist`, sent from a directory that holds its own `.specify/`, checks for
  a halt in that directory but rebuilds the repository `dist/`. Only test
  fixtures hold a nested `.specify/` today, and the orchestrator runs the runner
  from the worktree root, so supported runs do not reach this. Both root finders
  predate this PR.
- The sweep isolation helper runs in `read_only` mode, yet on an isolation
  failure it writes the halt record. Its response still reports no state
  writes. The record is the intended effect: it is the only write, it is
  git-ignored, and it only adds a refusal.
- When an existing halt record cannot be read, the sweep isolation failure
  raises instead of returning its `isolation_boundary_unavailable` envelope.
  The runner answers `internal_failure`. This still fails closed: every later
  apply request refuses while the record stays unreadable.
- `apply_refusal` returns no refusal when the runner cannot resolve the
  repository root. Every dispatch path then rejects the same request for that
  root, so no write follows.
