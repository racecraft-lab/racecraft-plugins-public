# Quickstart: PRSG-011 Retro-migration

## Repository Migration Dry-Run

```bash
speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh --dry-run --repo-root .
```

Expected result:

- One compact JSON report.
- No file changes.
- Dirty trees are allowed.
- Pending or no-op marker and Tier-0 navigation decisions are listed.

## Repository Migration Apply

```bash
speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh --apply --repo-root .
```

Expected result:

- Fails before backup or mutation if `git status --porcelain=v1 --untracked-files=all` is non-empty.
- Creates a forced backup outside the repo.
- Writes `.specify/structure-version.json` with `{"structureVersion":1}` when needed.
- Regenerates roadmap-MOC navigation through `generate-spec-index.sh`.
- Prints the backup path in the JSON report.
- On an already-current repository, reports no-op without creating a backup,
  writing files, or regenerating generated zones.

## Tier-2 Relocation Dry-Run

```bash
speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh --dry-run --spec specs/<spec-dir> --repo-root .
```

Expected result:

- One compact JSON report.
- No file changes.
- Dirty trees are allowed.
- Proposed PROCESS moves, CONTRACT protections, evidence normalization, docs-side anchor moves, stamp decisions, generated updates, and collision blocks are listed.

## Tier-2 Relocation Apply

```bash
speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh --apply --spec specs/<spec-dir> --repo-root .
```

Expected result:

- Fails before backup or mutation on dirty trees, invalid active-feature state,
  frozen/in-flight target specs, missing `SPEC-MOC.md`, or target collisions.
- Creates a forced backup outside the repo.
- Moves only approved PROCESS artifacts.
- Leaves CONTRACT artifacts in place.
- Stamps `SPEC-MOC.md` with `structureVersion: 1`.
- Normalizes legacy evidence to `.process/evidence/verification-evidence.md`.
- Canonicalizes `pr-review-packet.md` and legacy `peer-review-*` to
  `.process/pr-review-packet.md`.
- Fails before backup or mutation when competing evidence or review-packet
  sources would overwrite the same canonical target.
- Regenerates generated links/index through `generate-spec-index.sh`.
- On an already-current target, reports no-op without creating a backup,
  moving files, stamping `SPEC-MOC.md`, or regenerating links/index.

## Recovery

Each apply report includes a backup path and restore hint. Use the reported
backup path to restore the pre-mutation file state if relocation or repository
migration must be rolled back. If a failure happens after backup creation, the
JSON report names the created backup path and includes a restore hint; failures
before mutation report no backup and no recovery action.

## Expected Skill Guidance

`speckit-upgrade` should surface the repository migration sequence exactly:

```bash
speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh --dry-run --repo-root .
speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh --apply --repo-root .
```

The dry-run command comes first. The apply command is the safe follow-up only
after the operator reviews pending/skipped/no-op output and has a clean tree.

`speckit-scaffold-spec` and `speckit-autopilot` should surface Tier-2 relocation
only as a suggestion:

```bash
speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh --dry-run --spec specs/<spec-dir> --repo-root .
speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh --apply --spec specs/<spec-dir> --repo-root .
```

They do not run either command automatically. Claude Code and Codex skill
surfaces must describe the same command sequence and safety guarantees.

## Focused Verification

```bash
bash tests/speckit-pro/run-all.sh --layer 1
bash tests/speckit-pro/run-all.sh --layer 4
bash tests/speckit-pro/run-all.sh
```

Additional coverage for this spec:

- Layer 4 fixtures for dry-run no-mutation, apply dirty-tree block,
  idempotency, move-set allow-list, dual-anchor relocation, evidence
  normalization, in-flight skip, ID normalization, and out-of-scope
  non-SpecKit/date-first namespace skip reporting with no Tier-0 rows or Tier-2
  move candidates.
- Layer 3 fixtures for scaffold/autopilot suggestion behavior, including no
  suggestions for out-of-scope namespaces, plus `speckit-upgrade` repository
  migration guidance.
- Layer 8 parity checks for mirrored Claude Code/Codex skill prose covering the
  exact command sequences and no-auto-run guarantees.

Verified implementation results:

- `bash tests/speckit-pro/run-all.sh --layer 1` -> 887/887 passed.
- `bash tests/speckit-pro/run-all.sh --layer 4` -> 881/881 passed.
- `bash tests/speckit-pro/run-all.sh` -> 1958/1958 passed.
- `bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run` -> 6 passed, 0 failed, 0 skipped.
