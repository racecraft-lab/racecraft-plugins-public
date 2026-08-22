# Quickstart: ART-017 Validation

This guide describes the validation path for implementation. It is not an implementation script.

## Prerequisites

- Work on branch `art-017-state-bookkeeping-checks`.
- Use Python 3.11+.
- Install `docs-site` dependencies once before docs reference commands if the worktree does not already have them:

```bash
pnpm --dir docs-site install --frozen-lockfile
```

## Targeted RED Check

After adding the ART-017 tests and before changing runtime behavior, run:

```bash
python3 tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py
```

Expected result before implementation:

- The three new status-evidence negative controls fail because their reported keys do not yet move the scoped exit code.
- The gated-verdict consistency test fails if verdicts are changed without matching rule membership, or rule membership changes without matching verdicts.

## Targeted GREEN Check

After updating the validator rule tuple and the three intent records atomically, run:

```bash
python3 tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py
```

Expected result after implementation:

- Clean control exits `0` under `--rule status-evidence`.
- Each of `in_progress_errors`, `duplicate_state_steps`, and `state_order_errors` independently exits `1`.
- In each isolated mutation, the other two ART-017 problem lists remain empty.
- Legacy state coverage debt remains visible in the report but nonblocking under `status-evidence`.
- Tracked authority-matched workflow/state pairs pass the exact scoped invocation.

## Release Artifact Refresh

After authored source/test/prose changes are green, regenerate derived plugin surfaces:

```bash
python3 scripts/refresh-release-artifacts.py
pnpm --dir docs-site reference:generate
pnpm --dir docs-site reference:check
```

Expected result:

- Generated Claude/Codex payloads, installed-cache fixtures, proof/evidence files, and docs references match the authored source tree.
- No generated payload, proof, installed-cache, or reference file is hand-edited.

## Full Verification

Run the repository suite before ready or merge:

```bash
python3 tests/speckit-pro/run-all.py
```

Expected result:

- Layers 1, 4, and 5 pass with zero failures.
- Any docs reference check required by changed generated references passes.

## Final Integration Boundary

If ART-008 lands first, ART-017 must rebase onto latest `main`, regenerate shared derived artifacts, run docs reference generation/checking, and rerun the full suite before the PR is marked ready or merged.
