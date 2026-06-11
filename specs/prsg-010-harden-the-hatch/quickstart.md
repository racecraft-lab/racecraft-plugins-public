# Quickstart: PRSG-010 Validation

## Prerequisites

- Work from the `prsg-010-harden-the-hatch` branch.
- Ensure `bash`, `jq`, `git`, and the repository test fixtures are available.
- Use `specs/prsg-010-harden-the-hatch/` as the feature artifact directory.

## Baseline structural check

```bash
bash tests/speckit-pro/run-all.sh --layer 1
```

Expected outcome:

- Layer 1 passes.
- Structural checks accept the new contracts, skill mirrors, templates, and
  script layout.

## Script-unit validation

```bash
bash tests/speckit-pro/run-all.sh --layer 4
```

Expected outcome:

- Final backstop fixtures prove pass/warn/exception proceed.
- Final backstop fixtures prove `block` or exit 1 without honored exception
  stops before PR body generation, `gh pr create`, and `multi-pr-emission.sh`.
- Final backstop fixtures prove exit 2 stops as gate error without a
  re-slicing packet.
- O5 topology fixtures cover valid parent, missing child, duplicate child,
  nested child path, unknown dependency, later-child dependency, and cycle.
- Atomicity router fixtures cover guarded cutover, release-held cutover,
  branch-by-abstraction, weak evidence, and conflict hints.

## Contract validation

Validate feature-level schemas with a JSON Schema validator available in the
developer environment, or through the Layer 4 tests that exercise these schemas:

```bash
bash tests/speckit-pro/layer4-scripts/test-final-reviewability-backstop.sh
bash tests/speckit-pro/layer4-scripts/test-o5-topology.sh
bash tests/speckit-pro/layer4-scripts/test-atomicity-route.sh
```

Expected outcome:

- Re-slicing packets validate against
  `contracts/reslicing-packet.schema.json`.
- Final gate state validates against
  `contracts/final-reviewability-gate-state.schema.json`.
- O5 manifests validate against `contracts/o5-parent-manifest.schema.json`.
- Router output validates against `contracts/routing-decision.schema.json`.

## Mirror and parity validation

Run Layer 8 parity when Claude and Codex skill prose changes:

```bash
bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh
```

Expected outcome:

- Claude and Codex autopilot guidance both stop before PR creation on an
  unexcepted final gate block.
- Claude and Codex scaffold/status guidance both use flat O5 child specs and
  parent-manifest rollup.
- Both surfaces preserve typed exceptions and reject generated boilerplate.

## Default verification

```bash
bash tests/speckit-pro/run-all.sh
```

Expected outcome:

- Default deterministic layers pass.
- The implementation is ready for the PRSG-010 split-stack review packet.
