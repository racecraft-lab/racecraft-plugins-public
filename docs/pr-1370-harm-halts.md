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
