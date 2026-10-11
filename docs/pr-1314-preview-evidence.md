# Preview evidence security fix

Finding `F1314-f09415bc` concerns false preview evidence: an unrelated value
or file digest could stand in for the named surface observation. Terminal
preview answers require `values.surface`: `verified` names the observed
surface, while `unavailable` names its absence with `none`. Saved evidence
must satisfy the same rule as a new observation.

The readiness writer and preview reader share the policy in
`require_surface_fingerprint`. Both hosts use this runner policy. Unrelated
values and file fingerprints remain supplementary evidence, never a
replacement for the surface observation.

## Known limits

- Surface labels are caller observations, not independently authenticated
  capability proofs. A caller authorized to assert a status can also supply
  its matching label; this change closes missing and contradictory evidence,
  without claiming to prevent a caller from lying about its tools. The
  reported `verified/none` and `unavailable/browser` contradictions add no
  access for that reason, but are nevertheless rejected for consistency.
- `unknown` and `not_applicable` intentionally need no surface label. Neither
  status can reach the terminal preview branch: read-back is `unknown`, so
  observer dispatch remains enabled.
- Empty observations and missing or unreadable files alone cannot establish
  a terminal preview answer. Links and renamed files cannot replace the
  `value:surface` fingerprint. Existing record binding, trusted-file reading,
  file freshness, and malformed-evidence checks still apply.
- Live session capability discovery and a real headless canary were not
  exercised. The tests exercise runner requests, saved-record read-back,
  and artifact observer dispatch on both hosts. Linux VM results do not
  cover the orchestrator's macOS sandbox checks.
