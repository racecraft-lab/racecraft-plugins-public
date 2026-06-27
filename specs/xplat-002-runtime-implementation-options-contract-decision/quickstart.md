# Quickstart: Review the XPLAT-002 Plan Artifacts

This guide validates the Plan-phase artifacts for the runtime decision spike.
It does not run or implement a `speckit-pro-runner`.

## 1. Confirm Worktree and Branch

```bash
git rev-parse --abbrev-ref HEAD
git status --short
```

Expected branch:

```text
codex/xplat-002-runtime-implementation-options-contract-decision
```

## 2. Confirm Required Plan Artifacts Exist

```bash
test -f specs/xplat-002-runtime-implementation-options-contract-decision/plan.md
test -f specs/xplat-002-runtime-implementation-options-contract-decision/research.md
test -f specs/xplat-002-runtime-implementation-options-contract-decision/data-model.md
test -f specs/xplat-002-runtime-implementation-options-contract-decision/contracts/speckit-pro-runner-contract.md
test -f specs/xplat-002-runtime-implementation-options-contract-decision/quickstart.md
```

## 3. Check for Unresolved Markers

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/count-markers.sh gaps specs/xplat-002-runtime-implementation-options-contract-decision
```

Expected result: `"total":0`.

## 4. Review Decision-Readiness Coverage

Confirm the artifacts cover:

- JavaScript/TypeScript, Python, and small per-platform binary candidates.
- XPLAT-001 must-have gates and weighted criteria.
- Installed-cache reliability as a pass/fail gate.
- Documentation evidence plus bounded non-mutating probe expectations, including
  installed Claude and installed Codex plugin-cache invocation evidence or
  host-specific evidence gaps.
- Structured fallback handling for probes that cannot be run locally, including
  missing probe, host/runtime scope, reason unavailable, substitute evidence,
  gate or scoring effect, owner, and expiry/removal or follow-up condition.
- Objective close-candidate tie-breaker rules: weighted totals within five
  points or a non-reliability-only score lead, followed by ordered reliability
  inputs before maintainer preference.
- `speckit-pro-runner` entrypoint and default `scripts/speckit-pro-runner`
  payload-relative path.
- JSON stdin/stdout envelopes, line-delimited JSON stderr diagnostics, shared
  exit-code map, typed paths, shell-disabled subprocess rules, installed-payload
  helper dispatch, runtime-info or preflight, and fixture parity expectations.
- Fixture parity assertions that identify expected stdout `status`, process
  `exit_code`, stderr diagnostic `code`, and response-field behavior for
  invalid JSON, missing required fields, missing prerequisites, subprocess
  nonzero, subprocess timeout, and stderr-only failure.
- XPLAT-003 supply-chain implication matrix handoff without selected controls,
  including evidence-backed versus assumed dependency/artifact shape and any
  unknown or unverified assumptions recorded as evidence gaps.
- XPLAT-004 selected-runtime, command-contract, adapter-record, fixture-parity,
  and XPLAT-001 row-derived implementation input handoff.
- Public support-claim boundary: no README, docs-site, marketplace metadata,
  changelog, release-note, or public support promise edits.

## 5. Check Diff Hygiene

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh diff origin/main...HEAD
git diff --name-only
git diff --check
```

Expected reviewability status is `pass` or `warn` with no blockers. Expected
changed files are Plan-phase artifacts in the feature directory plus the
command-required agent context pointer.

## 6. Implementation-Phase Evidence Expectations

When XPLAT-002 moves to implementation, the decision record or linked evidence
must record probe results or evidence gaps for:

- runtime availability/version
- installed Claude plugin-cache invocation
- installed Codex plugin-cache invocation
- supplemental source or generated-payload invocation, only when useful to
  explain setup and never as a replacement for installed-cache evidence
- JSON stdin/stdout
- stderr/exit separation
- paths with spaces and Windows separators
- shell-disabled subprocess success, nonzero, timeout, and missing-command
  behavior
- structured fallback plans for any required local probe that cannot run, with
  evidence gaps not scored as installed-cache probe passes
- objective close-candidate reliability tie-breaker comparison covering
  installed Claude cache probe status, installed Codex cache probe status,
  post-cache setup burden, offline behavior, first-run/bootstrap diagnostics,
  runtime-info/preflight completeness, and unresolved tie handling
- exact failure assertions for malformed envelopes and subprocess failures:
  stdout `status`, process `exit_code`, stderr diagnostic `code`, and required
  response fields
- XPLAT-001 row-derived implementation inputs for XPLAT-004, including row IDs,
  owner buckets, active invocation modes, runner helper IDs, operations/modes,
  adapter records, fixture expectations, and explicit exclusions

The implementation evidence must still avoid runner implementation, helper
ports, active invocation-path changes, generated payload cutover, and public
native-platform support claims.
