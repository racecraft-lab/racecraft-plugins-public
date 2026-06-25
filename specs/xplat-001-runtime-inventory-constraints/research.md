# Phase 0 Research: Runtime Inventory and Constraints

## Decision: Use repo-local static scans, not a new scanner

**Rationale**: XPLAT-001 is an inventory/rubric spike. Existing Git and
ripgrep-style searches can exhaust tracked text without adding a persistent
automation layer that later specs would need to maintain.

**Alternatives considered**:

- New helper script: rejected because XPLAT-001 does not need reusable runtime
  behavior and no new helper should be shipped before the runtime decision.
- Manual-only review: rejected because the report must prove coverage of the
  whole-repo result set.

## Decision: Publish one Markdown report under `docs/ai/research/`

**Rationale**: The setup decisions and spec require durable review-visible
output under `docs/ai/research/`. A single report keeps inventory rows,
summary counts, runtime rubric, supply-chain rubric, and handoff notes together.

**Chosen target**: `docs/ai/research/cross-platform-runtime-inventory.md`

**Alternatives considered**:

- Spec-only artifacts: rejected because the accepted setup answer chose docs
  research for the durable deliverable.
- Mirrored docs and spec copies: rejected because duplicate reports create
  drift risk.

## Decision: Use Markdown tables with summary counts

**Rationale**: Reviewers need a readable PR artifact. Later XPLAT specs need
stable owner buckets and evidence, not a machine-ingested contract yet.

**Alternatives considered**:

- Markdown plus JSON: rejected for this slice because no concrete automation
  benefit has been proven.
- CSV appendix: rejected because rationale, traces, and exceptions are harder to
  review than in Markdown.

## Decision: Use a two-axis row model

**Rationale**: Physical/source classification and active-runtime proof are
different questions. Keeping them separate prevents public docs, generated
payloads, tests, fixtures, and archive matches from becoming false active
runtime blockers.

**Axes**:

- `classification`: where the reference lives or why it is excluded.
- `active_runtime_status`: whether static invocation evidence proves installed
  runtime relevance.

## Decision: Require static invocation traces for active runtime

**Rationale**: A text match alone is too noisy for a whole-repo scan. Proven
active runtime rows must cite caller-to-callee evidence from installed skills,
agents, hooks, generated payloads, or other installed plugin surfaces.

**Alternatives considered**:

- Text match is enough: rejected because it over-promotes docs, tests, fixtures,
  and archive references.
- Runtime probes: rejected because XPLAT-001 is static-only and runtime probes
  belong to XPLAT-002 or later.

## Decision: Keep candidate evidence separate from scoring

**Rationale**: XPLAT-001 enables XPLAT-002 and XPLAT-003. It defines criteria,
must-have gates, weights, and evidence targets but does not choose a runtime or
security model.

**Rejected outputs**:

- Candidate scores.
- Sample scoring.
- Ranked options.
- Winner selection.
- Required runtime or supply-chain controls.
