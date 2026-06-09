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
- Regenerates generated links/index through `generate-spec-index.sh`.

## Recovery

Each apply report includes a backup path and restore hint. Use the reported
backup path to restore the pre-mutation file state if relocation or repository
migration must be rolled back.

## Focused Verification

```bash
bash tests/speckit-pro/run-all.sh --layer 1
bash tests/speckit-pro/run-all.sh --layer 4
bash tests/speckit-pro/run-all.sh
```

Additional coverage for this spec:

- Layer 4 fixtures for dry-run no-mutation, apply dirty-tree block,
  idempotency, move-set allow-list, dual-anchor relocation, evidence
  normalization, in-flight skip, and ID normalization.
- Layer 3 fixtures for scaffold/autopilot suggestion behavior.
- Layer 8 parity checks for mirrored Codex skill prose.
