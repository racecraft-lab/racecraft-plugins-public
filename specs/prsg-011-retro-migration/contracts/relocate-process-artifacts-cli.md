# Contract: relocate-process-artifacts.sh

## Command

```bash
speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh (--dry-run|--apply) --spec <spec-dir> [--repo-root <path>]
```

Exactly one mode flag is required. `--spec <spec-dir>` is required.

## Purpose

Relocate PROCESS artifacts for one thawed legacy spec into the current
`.process/` anchors while keeping CONTRACT artifacts visible and unchanged.

## Inputs

| Input | Required | Rules |
|-------|----------|-------|
| `--dry-run` | one mode required | Read-only, allowed on dirty trees. |
| `--apply` | one mode required | Requires clean tree before backup or mutation. |
| `--spec <spec-dir>` | yes | Repo-relative or absolute path to the target spec directory. Must resolve inside repo root. |
| `--repo-root <path>` | optional | Defaults to the repository containing the plugin script. |

## Output

Stdout emits one compact JSON report matching
[migration-report-json.md](./migration-report-json.md). The report includes:

- exact proposed move set
- CONTRACT protections
- already-normalized `.process/**` no-ops
- evidence normalization decisions
- docs-side dual-anchor decisions
- generated-link/index updates
- dirty-tree state and apply-blocked reason
- stamp decision for `SPEC-MOC.md`
- backup path and recovery hint

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Successful dry-run, successful apply, or safe no-op. |
| `2` | Usage error, invalid repo/spec path, invalid active-feature state in apply, dirty-tree apply block, missing/non-regular `SPEC-MOC.md`, target collision, backup failure, move failure, stamp failure, or generator failure. |

## Dry-Run Behavior

- Does not create, edit, move, stamp, or regenerate files.
- Allowed on dirty trees.
- Reports proposed `git mv` operations in deterministic order.
- Reports planned backup path without creating it.
- Reports target-path collisions and whether apply would be blocked.
- Reports valid in-flight specs as frozen and does not suggest relocation for them.

## Apply Behavior

1. Resolve repo root and target spec directory.
2. Parse active-feature state.
3. Verify target `SPEC-MOC.md` exists and is a regular file.
4. Detect every move, protection, no-op, generated update, and collision before
   mutation.
5. Exit before backup or mutation if active-feature state is invalid.
6. Exit before backup or mutation if target is frozen/in-flight.
7. Exit before backup or mutation if any target-path collision exists.
8. Run dirty-tree check and exit before backup or mutation if dirty.
9. Create forced backup outside the repo and record the path.
10. Move only approved PROCESS artifacts.
11. Stamp `SPEC-MOC.md` with bare integer `structureVersion: 1`.
12. Regenerate affected links/index through `generate-spec-index.sh`.
13. Emit the final JSON report.

## PROCESS Allow-List

Tier-2 may move only root-relative PROCESS artifacts with these names or
patterns:

- `retrospective.md`
- `*-report.md`
- `uat-*`
- `pr-review-packet.md`
- `peer-review-*`
- `cleanup-report.md`
- `analysis.md`
- `evidence/`
- `verification-evidence.md`
- `design-concept.md`
- `*-design-concept.md`
- `workflow.md`
- `*-workflow.md`

Already-normalized `.process/**` files are reported as no-op.

## CONTRACT Protections

These artifacts remain in place even when their names resemble PROCESS files:

- `spec.md`
- `plan.md`
- `tasks.md`
- `research.md`
- `data-model.md`
- `quickstart.md`
- `contracts/**`
- `checklists/**`
- `SPEC-MOC.md`

CONTRACT protection always wins over the PROCESS allow-list.

## Evidence Normalization

- Root `verification-evidence.md` moves to `evidence/verification-evidence.md`
  when the target is absent.
- If both source and target exist, dry-run reports a collision and apply fails
  before mutation.
- If only `evidence/verification-evidence.md` exists, relocation reports an
  already-normalized no-op.

## Dual PROCESS Anchors

- Files under `--spec <spec-dir>` move to `<spec-dir>/.process/`.
- Matching docs-side files in `docs/ai/specs/` move to
  `docs/ai/specs/.process/` only when the basename matches the thawed spec ID:
  `<SPEC-ID>-design-concept.md` or `<SPEC-ID>-workflow.md`.
- Unrelated docs files, technical roadmaps, PRDs, already-current `.process/`
  files, and CONTRACT artifacts are not moved.

## Idempotency

After successful relocation, dry-run and apply report no-op current state. No
additional moves, stamps, or backups occur on a clean already-current target.
