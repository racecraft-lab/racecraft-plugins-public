# UAT Runbook: XPLAT-009

| Field | Value |
|-------|-------|
| Spec | XPLAT-009 |
| Branch | codex/xplat-009-plugin-source-and-payload-bash-eradication |
| PR | https://github.com/racecraft-lab/racecraft-plugins-public/pull/297 |
| Generated from | 2026-07-07 post-implementation verification |

This runbook verifies plugin source and generated payload Bash eradication only.
It does not complete XPLAT-008 native Windows/macOS/Linux operator UAT.

## Env Setup

Run these commands from the repository root on a clean checkout of the PR branch:

1. `python3 --version`
   Expected: Python 3.11 or newer.
2. `git status --short`
   Expected: no local edits before UAT starts.

## Per-Story Acceptance Tests

1. Verify source Bash removal:
   `find speckit-pro -type f -name '*.sh'`
   Expected: no output.

2. Verify generated payload Bash removal:
   `find dist/claude/speckit-pro dist/codex/speckit-pro -type f -name '*.sh'`
   Expected: no output.

3. Verify the deterministic suite:
   `bash tests/speckit-pro/run-all.sh`
   Expected: `speckit-pro test suite: 2021/2021 passed`.

4. Inspect zero-Bash guard evidence:
   `python3 -m json.tool docs/ai/specs/.process/XPLAT-009-zero-bash-guard-result.json`
   Expected: `status` is `ok`, `gate_status` is `pass`, `blocking_count` is `0`, and `script_file_count` is `0`.

5. Inspect installed-cache proof:
   `python3 -m json.tool docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`
   Expected: every proof record is source-derived, not mutable user-cache evidence, and reports zero script files.

## FR Coverage Matrix

| Requirement | UAT Step |
|-------------|----------|
| FR-001 through FR-005 | Steps 1, 3, and 4 |
| FR-006 through FR-008 | Steps 2 and 5 |
| FR-009 through FR-012 | Steps 3, 4, and 5 |

## Negative-Path Tests

1. Review `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/zero-bash-guard-cases.json`.
   Expected: cases cover blocking active `.sh`, Bash, and `jq` findings, while historical/archive allowlist entries remain excluded from release-ready proof.

2. Confirm release readiness preserves the XPLAT-008 native UAT boundary:
   `python3 -m json.tool docs/ai/specs/.process/XPLAT-009-release-readiness-result.json`
   Expected: the XPLAT-009 zero-Bash gate passes without claiming completed public native-platform UAT.

## Self-Review Findings

- Full suite passed after updating the XPLAT-004/XPLAT-008 runner guard to recognize XPLAT-009's declared zero-Bash source/payload boundary.
- RepoPrompt review-agent launch failed with `Transport closed`; parent-session review completed instead.

## Sign-off

Advisory only. These checkboxes block nothing.

- [ ] Reviewer confirmed source and generated payload `find` commands return no `.sh` files.
- [ ] Reviewer confirmed the full deterministic suite passes.
- [ ] Reviewer confirmed zero-Bash and installed-cache proof evidence.

## Rollback

Revert the XPLAT-009 branch. Do not partially restore deleted `.sh` files without
also restoring the matching active guidance, generated payloads, tests, and
release-readiness evidence from the same commit.
