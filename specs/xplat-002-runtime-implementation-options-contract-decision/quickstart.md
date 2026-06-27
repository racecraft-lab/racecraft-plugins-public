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
rg -n 'NEEDS CLARIFICATION|\\[Gap\\]|\\[CRITICAL\\]' specs/xplat-002-runtime-implementation-options-contract-decision
```

Expected result: no matches.

## 4. Review Decision-Readiness Coverage

Confirm the artifacts cover:

- JavaScript/TypeScript, Python, and small per-platform binary candidates.
- XPLAT-001 must-have gates and weighted criteria.
- Installed-cache reliability as a pass/fail gate.
- Documentation evidence plus bounded non-mutating probe expectations.
- `speckit-pro-runner` entrypoint and default `scripts/speckit-pro-runner`
  payload-relative path.
- JSON stdin/stdout envelopes, line-delimited JSON stderr diagnostics, shared
  exit-code map, typed paths, shell-disabled subprocess rules, runtime-info or
  preflight, and fixture parity expectations.
- XPLAT-003 supply-chain implication matrix handoff without selected controls.
- XPLAT-004 selected-runtime and command-contract handoff.
- Public support-claim boundary: no README, docs-site, marketplace metadata,
  changelog, release-note, or public support promise edits.

## 5. Check Diff Hygiene

```bash
git diff --name-only
git diff --check
```

Expected changed files are Plan-phase artifacts in the feature directory plus
the command-required agent context pointer.

## 6. Implementation-Phase Evidence Expectations

When XPLAT-002 moves to implementation, the decision record or linked evidence
must record probe results or evidence gaps for:

- runtime availability/version
- source or installed-cache invocation
- JSON stdin/stdout
- stderr/exit separation
- paths with spaces and Windows separators
- shell-disabled subprocess success, nonzero, timeout, and missing-command
  behavior

The implementation evidence must still avoid runner implementation, helper
ports, active invocation-path changes, generated payload cutover, and public
native-platform support claims.
