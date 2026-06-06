# Quickstart: MOC templates + scaffold-time skeleton + version-gated lints

How a maintainer runs and verifies this feature. Everything is deterministic bash + jq; there is no build/typecheck/lint step in this repo.

## Verify the whole feature

From the `speckit-pro/` directory:

```bash
bash tests/run-all.sh
```

This runs Layers 1, 4, and 5. The two new lints run inside Layer 1 (against committed fixtures AND this repo's real spec trees); the shared normalizer's unit test runs inside Layer 4. A green run means:

- the lints find no violations in any version-gated spec (legacy specs are exempt and skipped),
- PRSG-002's own `specs/prsg-002-moc-templates/SPEC-MOC.md` resolves its `up:` and passes the `spec_id` check,
- the normalizer's edge cases (`PRSG-002`!=`SPEC-002`, `013a`!=`013a1`, `006a`, no-prefix→`spec`) all pass.

Run just the structural layer (fast):

```bash
bash tests/run-all.sh --layer 1
```

Run just the normalizer unit test:

```bash
bash tests/run-all.sh --layer 4
```

## What the lints check

- **Orphan** (`tests/layer1-structural/validate-moc-orphan.sh`): every version-gated `SPEC-MOC.md` has a present, well-formed relative `up:` (not a wikilink). Non-MOC docs are not required to carry `up:`.
- **Stale-index** (`tests/layer1-structural/validate-moc-stale-index.sh`): every relative `[]()` target in a version-gated MOC — including the `up:` value and any body links — resolves to an existing file; any `[[wikilink]]` is a violation.
- **spec_id**: each version-gated `SPEC-MOC.md`'s `spec_id` namespace-matches its directory (shared normalizer).

A spec with no `SPEC-MOC.md`, or a marker with no `structureVersion`, is silently skipped (grandfathered).

## Scaffold a spec and confirm the marker

When `speckit-scaffold-spec` runs for a new spec, it writes a minimal marker into the branch-named contract dir:

```bash
# After scaffolding SPEC-ID on branch <branch-name>:
cat specs/<branch-name>/SPEC-MOC.md
```

Expect frontmatter with a non-empty relative `up:` pointing at the existing `*-technical-roadmap.md`, `structureVersion: 1`, and a `spec_id` that namespace-matches `<branch-name>`. For PRSG-002 itself:

```yaml
---
up: "[roadmap](../../docs/ai/specs/pr-size-governance-technical-roadmap.md)"
spec_id: PRSG-002
structureVersion: 1
---
```

## Templates

Two shapes live next to `workflow-template.md`:

```bash
ls speckit-pro/skills/speckit-coach/templates/roadmap-moc-template.md \
   speckit-pro/skills/speckit-coach/templates/spec-moc-template.md
```

Each carries the full six-field contract (`up`, `related`, `status`, `rank`, `spec_id`, `structureVersion`); only `up`/`structureVersion`/`spec_id` are enforced in v1.

## Manual sanity checks (optional)

Confirm a version-marked MOC with a dangling link fails (use a fixture, not a real spec):

```bash
bash tests/layer1-structural/validate-moc-stale-index.sh   # exits nonzero if any fixture/real MOC has an unresolved relative link or a wikilink
```

Confirm a no-marker directory is skipped: a spec dir without `SPEC-MOC.md` contributes no violation — the full Layer-1 run stays green on legacy specs.
