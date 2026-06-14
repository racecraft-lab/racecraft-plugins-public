# PRSG-014 PR Packet Notes

## Traceability

- Spec: `specs/prsg-014-optional-gh-stack-stack-manager-integration/spec.md`
- Plan: `specs/prsg-014-optional-gh-stack-stack-manager-integration/plan.md`
- Tasks: `specs/prsg-014-optional-gh-stack-stack-manager-integration/tasks.md`
- Shared detector: `speckit-pro/skills/speckit-autopilot/scripts/detect-stack-manager.sh`
- Shared schema: `speckit-pro/skills/speckit-autopilot/contracts/stack-manager-decision.schema.json`
- Emission integration: `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh`
- Restack integration: `speckit-pro/skills/speckit-autopilot/scripts/restack.sh`
- Guidance parity: `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` and `speckit-pro/codex-skills/speckit-autopilot/`

## Review Order

1. Shared contract and detector.
2. Emission state and command-plan threading.
3. Restack apply-mode detection and output threading.
4. Layer 4, Layer 7, and Layer 8 fixtures.
5. Claude Code and Codex guidance parity.

## Rollback

Revert the detector, schema fields, emission/restack wiring, and PRSG-014
fixtures together. Existing explicit `gh pr create/edit --base --head
--body-file` behavior remains the fallback path, so rollback should restore the
pre-PRSG-014 behavior without requiring operator data migration.

## Feature Flag

No runtime feature flag is required. `gh-stack` remains optional and is selected
only when `detect-stack-manager.sh` proves supported version, read-only proof,
validated packet/topology evidence, and safe mutation boundaries. Otherwise the
existing explicit `gh` path is used before mutation.

## Known Gaps

- Layer 7 PRSG-014 coverage is replay-only and intentionally live-safe; it does
  not invoke networked GitHub or live `gh stack`.
- Partial-mutation recovery is represented in deterministic decision and
  scenario evidence; live recovery should still be reviewed carefully by an
  operator before resuming a stack.
- `gh stack submit` remains out of scope because PRSG-012 packet-owned title and
  body semantics stay authoritative.
