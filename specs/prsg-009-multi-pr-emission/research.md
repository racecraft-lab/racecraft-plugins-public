# Research: PRSG-009 multi-PR emission

## Decision: Use PRSG-008 layer-plan output as the only slice source

**Rationale**: PRSG-009 is an emission feature, not a routing feature. Reusing
`plan-layers.sh` output keeps branch order, file scope, and review slices aligned
with PRSG-008 and avoids conflicting atomicity rules.

**Alternatives considered**:
- Recompute slices from changed files during emission. Rejected because it
  duplicates PRSG-008 heuristics and could produce different review units.
- Allow manual slice definitions in PRSG-009. Rejected because resume and PRS
  evidence would no longer be tied to the authoritative layer plan.

## Decision: Split machine state from reviewer-facing PRS rows

**Rationale**: `autopilot-state.json` needs durable resume detail, failure
evidence, retry policy, and reconciliation facts. `.process/prs.json` needs only
bounded reviewer-navigation rows for the generated Spec MOC PR table.

**Alternatives considered**:
- Store all emission state in `.process/prs.json`. Rejected because the MOC
  manifest would become bulky and operator-specific.
- Generate the MOC table from workflow prose. Rejected because prose is not a
  safe resume or reconciliation source.

## Decision: Use Style B incremental stack branches with explicit PR refs

**Rationale**: The first slice targets the integration base and each later slice
targets the previous slice branch. Explicit `gh pr create --base --head
--body-file` removes default-branch ambiguity and makes resume reconciliation
keyed by expected head/base refs.

**Alternatives considered**:
- Create sibling PRs all targeting the integration base. Rejected because later
  slices can depend on earlier slice changes.
- Rely on `gh pr create` defaults. Rejected because defaults are not stable
  enough for deterministic stack emission.

## Decision: Extend `generate-pr-body.sh` with optional `--slice-packet`

**Rationale**: Existing positional invocation must remain compatible for
single-PR specs. A JSON packet lets multi-PR emission add slice-specific fields
without creating a second PR body generator.

**Alternatives considered**:
- Replace the positional interface. Rejected because existing callers and tests
  depend on it.
- Add many individual flags. Rejected because the packet is easier to validate,
  store, and pass to MOC/PRS generation.

## Decision: Define scoped verification as recorded local evidence

**Rationale**: PRSG-009 scoped CI means per-slice verification commands and
evidence recorded in state, PR packets, PR bodies, and PRS rows. Existing GitHub
PR Checks continue unchanged, and full regression verification runs once before
emission.

**Alternatives considered**:
- Modify `.github/workflows/pr-checks.yml` to create per-slice jobs. Rejected by
  accepted clarification and because it would widen the feature into CI design.
- Run the full suite for every slice. Rejected because it conflates full
  regression confidence with per-slice review evidence.

## Decision: Make restack dry-run-first with optional `gh-stack`

**Rationale**: `gh-stack` can be used only when safely detected against an
existing active stack. The fallback `restack.sh` must be deterministic, emit JSON
stdout, keep diagnostics on stderr, and require `--apply` for mutation.

**Alternatives considered**:
- Require `gh-stack`. Rejected because it is optional tooling and PR creation
  still uses explicit `gh pr create`.
- Mutate by default. Rejected because restack happens during review recovery and
  should be inspectable before changing branches.

## Decision: Preserve Claude/Codex parity through mirrored references

**Rationale**: The user-facing behavior is documented in both Claude and Codex
autopilot references. The implementation must update both mirrors and rely on
Layer 1 parity checks to prevent drift.

**Alternatives considered**:
- Update only Claude reference files. Rejected because Codex users would receive
  stale post-implementation instructions.
- Move the behavior into generated distribution mirrors first. Rejected because
  source mirrors must be authoritative.
