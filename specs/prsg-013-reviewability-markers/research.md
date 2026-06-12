# Research: Non-Stopping Reviewability Markers

## Decision: Treat parseable reviewability sizing as marker input

**Decision**: Autopilot will treat parseable `pass`, `warn`, honored `exception`, and size-only `status=block` reviewability results as PR-marker planning input when all correctness and safety gates are valid.

**Rationale**: Reviewability sizing is a scope-shaping signal. The product bug is caused by interpreting size-only reviewability results as implementation stops.

**Alternatives considered**:
- Keep task reviewability blocking: rejected because it stops valid implementation.
- Make all gates non-stopping: rejected because malformed plans, failed verification, unsafe output, invalid packets, unusable evidence, and stale state must still stop.

## Decision: Keep `reviewability-gate.sh tasks` compatible

**Decision**: Do not change the stable task-mode exit-code contract unless implementation proves a compatibility-safe extension is necessary. Autopilot captures stdout and exit code, parses valid `status=block` JSON, and converts size-only task blocks into marker-planning evidence.

**Rationale**: Existing callers may depend on the gate script returning nonzero for task-mode block results. The safer blast radius is in autopilot's caller handling.

**Alternatives considered**:
- Change task mode to exit 0 for blocks: rejected because it may silently change lower-level tooling behavior.
- Add a new marker mode immediately: rejected as unnecessary unless tests prove caller wrapping is insufficient.

## Decision: Derive default markers from Foundation and user-story sections

**Decision**: Marker planning creates `foundation` when Foundation tasks exist and one marker per user-story section. Small Polish tasks fold into the nearest appropriate non-Polish marker.

**Rationale**: Foundation and user-story sections already express reviewer-relevant task boundaries. Keeping Polish folded avoids cleanup-only PRs that add review overhead without user value.

**Alternatives considered**:
- Stories only: rejected because shared setup work may be too broad to hide in US1.
- Every phase marker: rejected because small cleanup-only PRs make review order noisier.
- Manual marker comments in `tasks.md`: rejected because marker state should be durable, validated, and fingerprinted outside generated prose.

## Decision: Persist top-level `pr_marker_plan`

**Decision**: Autopilot persists a top-level `pr_marker_plan` object in `autopilot-state.json` and mirrors it into workflow evidence. The plan includes schema version, status, source fingerprint, ordered markers, and structured warnings.

**Rationale**: Final PR emission needs durable state across resume and must detect stale markers when tasks, reviewability evidence, or hazard decisions change.

**Alternatives considered**:
- Store only workflow prose: rejected because it is hard to validate mechanically.
- Infer markers at final emission: rejected because implementation order and checkpoint evidence must be marker-aware earlier.

## Decision: Use ordered marker IDs and one-based review order

**Decision**: Marker IDs are `foundation`, `us<N>`, `us<N>-part<M>`, and `full-spec` for hazard collapse. The `markers[]` order plus one-based `review_order` is authoritative.

**Rationale**: IDs remain stable for resume, while `review_order` makes review packet ordering explicit and independent of JSON object key order.

**Alternatives considered**:
- Use array index only: rejected because resume and PR packet traceability need stable IDs.
- Use arbitrary generated UUIDs: rejected because they are less readable in workflow evidence and PR packets.

## Decision: Subdivide oversized stories only at safe task-cluster boundaries

**Decision**: When a user-story marker exceeds budget, subdivide only if there is a contiguous task group inside the story with no dependency crossing, complete declared files/tests, no shared mutation or hazard signal, and preserved task order. If no safe boundary exists, keep the story marker and record a structured warning.

**Rationale**: Internal story subdivision improves reviewability only when it does not break implementation dependency order or hide shared mutation risk.

**Alternatives considered**:
- Always split by task count: rejected because it may create dependency-invalid PRs.
- Never subdivide stories: rejected because large stories would remain unnecessarily hard to review.

## Decision: Collapse emission only for hard atomic hazards

**Decision**: Hazard collapse triggers only when the recorded Atomicity Route has `route == single-atomic-PR` or `releasable == false`. `one-navigable-PR` with `releasable == true` does not collapse by itself.

**Rationale**: Reviewability should split by default. Only hard atomicity or release safety should override scoped PR emission.

**Alternatives considered**:
- Collapse for any non-split route: rejected because it would over-collapse safe review scopes.
- Stop for operator approval: rejected because reviewability and atomicity findings should shape output without stopping valid implementation.

## Decision: Final backstop emits `marker_split`

**Decision**: If the final full-diff reviewability backstop is size-blocked and the current `pr_marker_plan` is valid, the outcome is `marker_split`, the command exits 0, and the evidence is passed to marker-based PR emission.

**Rationale**: The final backstop validates that the full diff is too large, but the persisted markers are the planned remedy.

**Alternatives considered**:
- Stop and ask for manual re-slicing: rejected because marker planning already produced durable scoped boundaries.
- Ignore markers and emit one oversized PR with warning: rejected because it discards the scoped PR architecture.

## Decision: Implement and checkpoint in marker order

**Decision**: When markers are present, the Implement phase executes tasks, checkpoints evidence, and prepares emission packets in marker order. Under hazard collapse, implementation still follows original marker order, but emission maps those checkpoints into one `full-spec` PR.

**Rationale**: PR emission should not infer per-marker scope from one mixed implementation diff.

**Alternatives considered**:
- Implement freely and infer slices later: rejected because final diff membership is ambiguous.
- Checkpoint tests only: rejected because reviewers need changed files and task traceability per marker.

## Decision: Mirror touched guidance across Codex and source surfaces

**Decision**: Any changed source autopilot guidance must be mirrored into the Codex skill surface with equivalent behavior.

**Rationale**: PRSG-013 changes phase semantics that must remain consistent across Claude and Codex autopilot runs.

**Alternatives considered**:
- Update source skill only: rejected because Codex runs would preserve the old stopping behavior.

## Decision: Verification uses Layer 4 plus Layer 3

**Decision**: Add deterministic Layer 4 coverage for marker planning, state persistence, implementation ordering evidence, hazard collapse, marker-aware final backstop, and multi-PR emission. Add one Layer 3 functional eval for a valid oversized spec whose reviewability size is the only negative finding.

**Rationale**: The feature spans shell contracts and agent guidance. Script fixtures prove deterministic behavior; the functional eval guards the guidance-level non-stopping contract.

**Alternatives considered**:
- Layer 4 only: rejected because guidance can regress even when scripts pass.
- Full live dogfood PR emission as required proof: rejected because it is useful but too slow and external-state-dependent for the required acceptance proof.
