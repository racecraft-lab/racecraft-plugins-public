# Quickstart: generate-spec-index.sh

How to run the generator, read a staleness report, and review this change.

## Prerequisites

- `bash` + `jq` (already required by the repo; no new dependency).
- Run from the repository root (the script infers the repo root from its own
  location; an optional positional scan-root arg overrides it).

## Run the generator (write mode — the authoritative path)

```bash
# Rebuild the generated zones in every version-marked SPEC-MOC.md, in place.
bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh
```

What it does: discovers each version-marked `SPEC-MOC.md`, injects the three empty
GENERATED zones at the canonical anchor if missing, then fills them — INDEX
(dormant/empty here), PRS (from `specs/<branch>/.process/prs.json` or
empty-but-valid), BACKLINKS (a sorted reachability index of the spec's own
artifacts). Whole-zone replace; never a partial patch.

## Check staleness (read-only — what speckit-status uses)

```bash
# Regenerate in memory, diff against committed, report staleness, write nothing.
bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check
echo "exit: $?"   # 0 = current, 1 = stale, 2 = error
```

Interpreting the result:

- **exit 0** — committed maps match a fresh rebuild; the index is current.
- **exit 1** — a committed map is stale; output names which map/zone drifted. Run
  the write-mode command above to refresh, then commit.
- **exit 2** — a map note is malformed/unreadable or an internal error occurred;
  the message is on stderr. `--check` wrote nothing.

## Prove determinism (the L1 fixture's assertion, by hand)

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh
git diff --quiet specs/*/SPEC-MOC.md && echo "clean"      # first write may change files
bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh
git diff --quiet specs/*/SPEC-MOC.md && echo "zero diff on re-run"   # idempotent
```

## Verify (this is a bash/shell repo — no package manager)

```bash
# From the speckit-pro/ directory:
shellcheck skills/speckit-autopilot/scripts/generate-spec-index.sh
bash -n   skills/speckit-autopilot/scripts/generate-spec-index.sh
bash tests/run-all.sh            # Layers 1, 4, 5 — incl. the new L1 determinism fixture + L4 unit test
```

The two PRSG-002 lints (`validate-moc-orphan.sh`, `validate-moc-stale-index.sh`)
run inside Layer 1 and dogfood-scan the real spec trees; they MUST stay green
after the generator writes the dogfooded `prsg-002` / `prsg-003` maps (the G7
guarantee in plan.md).

## Review order (for the PR reviewer)

1. `contracts/sentinel-grammar.md` + `contracts/generator-cli.md` +
   `contracts/prs-manifest.schema.md` — the byte/exit/input contracts.
2. `generate-spec-index.sh` — the shared script (read the sentinel constants,
   `assemble_zone_block`, the renderers, the whole-zone splice, the `--check`
   diff path).
3. `tests/layer4-scripts/test-generate-spec-index.sh` +
   `tests/layer1-structural/validate-spec-index-determinism.sh` — the verification.
4. `spec-moc-template.md` (added zones) and the two SKILL.md edits + their Codex
   mirrors (behavior wiring).
5. The dogfooded `specs/prsg-002-moc-templates/SPEC-MOC.md` and
   `specs/prsg-003-spec-index/SPEC-MOC.md` — real generated output, lints green.

## Non-goals (do not look for these here)

Roadmap-level INDEX population (PRSG-004); live slice→PR#→SHA writing (PRSG-009);
legacy-spec backfill (PRSG-011); a cross-spec citation graph; `speckit-status`
writing any file.
