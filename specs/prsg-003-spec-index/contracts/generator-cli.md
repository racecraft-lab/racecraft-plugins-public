# Contract: generate-spec-index.sh CLI

Authoritative CLI + exit-code contract for the shared generator. Both
`speckit-status` and `speckit-autopilot` (and their Codex mirrors) invoke this one
script by absolute plugin path. `bash` + `jq` only; no new dependency.

## Location

```text
speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh
```

Single shared, runtime-agnostic copy — NOT duplicated into `codex-skills/`
(FR-020). Sibling of `reviewability-gate.sh` / `generate-pr-body.sh`.

## Invocation

```text
generate-spec-index.sh [--check] [REPO_ROOT]
```

| Arg | Meaning |
|-----|---------|
| `--check` | Read-only mode: regenerate zones in memory, diff against the committed `SPEC-MOC.md` files, report staleness, **write nothing** (FR-012). |
| (no `--check`) | Write mode: regenerate and write changed `SPEC-MOC.md` files in place; inject missing zones (FR-008). The authoritative write path used by the autopilot. |
| `REPO_ROOT` (optional positional) | Scan root override; defaults to the repository root inferred from the script location (so it is runnable in any consuming project, mirroring the PRSG-002 lints' optional scan-root arg). |

The script must begin with `#!/usr/bin/env bash` and `set -euo pipefail`
(constitution II); it reuses the canonical normalizer (FR-004) by sourcing
`moc-id-normalize.sh` and `moc-frontmatter.sh` from its co-located
`scripts/lib/` directory, so the libs ship inside the plugin alongside the
generator (the test tree at `tests/speckit-pro/` is not shipped to consumers).

## Exit-code contract (3-way enum — mirrors the PRSG-002 lints; FR-015)

| Exit | Meaning | Stream |
|------|---------|--------|
| `0` | **current/clean** — write mode wrote successfully (or nothing needed changing); `--check` found no drift on any in-scope map | stdout (summary) |
| `1` | **stale** — `--check` found a non-empty diff between committed and freshly-regenerated zones | stdout (which maps + which zones are stale) |
| `2` | **error** — a malformed/unreadable target, or an internal/operational failure | stderr (actionable message); never conflated with exit 1 (FR-016) |

- `--check` never writes, on ANY path including the error path (FR-012).
- A non-regular-file target (directory/symlink where a MOC is expected) → exit 2,
  no write-through (spec Edge Cases, FR-016).
- A version-marked map with an absent/empty `prs.json` renders an empty-but-valid
  PRS zone and does NOT raise exit 2 (FR-011).
- Internal-error discipline: `set -E` + an ERR trap maps an unexpected `set -e`
  failure to exit 2 on stderr (same pattern as the PRSG-002 lints).

## Consumer mapping

| Consumer | Mode | Action on each exit |
|----------|------|---------------------|
| `speckit-status` | `--check` | exit 0 → report index current (write nothing); exit 1 → surface "index stale — run regen" (write nothing, FR-013); exit 2 → surface an error line, write nothing |
| `speckit-autopilot` (phase-gate) | write | run at every phase boundary; if the write produced a non-empty `git diff`, fold the changed maps into the existing checkpoint commit (D4 message when standalone); exit 2 → surface and stop (do not commit a broken regen) |

## Determinism guarantees (FR-003, SC-001, SC-008, SC-009)

- Pure function of committed files: no `gh`, no network, no nondeterministic input
  at generation time. Succeeds offline (SC-008).
- Identical committed inputs → byte-identical output; a second consecutive write
  run yields a zero-byte `git diff` (SC-001).
- File enumeration is `LC_ALL=C sort`-ed before rendering, so output is identical
  across machines with different filesystem enumeration order (SC-009).

## Idempotency (FR-008)

Running write mode repeatedly on a map that already has the zones produces no
change after the first run (inject-once; whole-zone replace is stable). The
determinism fixture asserts re-run = zero diff (L1).
