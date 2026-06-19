# Research: TACD-003 Prerequisite and Documentation Messaging

## Decision 1: Prerequisite Advisory Shape

Use one successful prerequisite result named `capability_coverage`.

The result stays advisory-only: `pass=true`, no per-tool available/missing
inventory, and a message that names setup-facing capability categories rather
than specific optional tool providers.

**Rationale**: The setup contract should distinguish true prerequisite gates
from optional evidence quality. A capability advisory communicates confidence
impact without turning missing optional tools into a failed setup state.

**Alternatives rejected**:

- Keep the named optional-server report: rejected because it implies a fixed
  optional-tool contract.
- Emit one result per capability provider: rejected because it recreates a
  provider inventory and makes optional coverage look gate-like.

## Decision 2: Capability Categories

Use the four setup-facing categories from the clarification record:

- Codebase context
- Library documentation
- Web/domain research
- Source extraction

**Rationale**: These categories describe what evidence the workflow needs,
not which implementation or vendor provides it. They also map directly to the
fallback and confidence language users need during setup.

## Decision 3: Active Guidance Boundary

Update only active prerequisite and limitation guidance in the declared files.
Review the adjacent autopilot guide and entrypoint summaries for repeated active
preflight or limitation wording, but do not expand the edit set unless the plan
and reviewability budget are amended first.

**Rationale**: TACD-003 is a messaging alignment slice. Broad static
enforcement, eval expectation updates, and pointer coverage belong to TACD-004.

## Decision 4: Generated Payloads

Treat generated payloads as source-derived. Regenerate only when a declared
source edit requires parity, and record the regeneration command in the PR
packet if it happens.

**Rationale**: Direct generated-payload edits create drift and make review
harder. Source-first edits keep review traceability clear.

## Decision 5: Focused Verification

Extend `tests/speckit-pro/layer4-scripts/test-check-prerequisites.sh` for the
changed JSON behavior. Add narrow changed-doc assertions only if they remain
small and directly tied to the declared active guidance edits.

**Rationale**: This gives deterministic coverage for TACD-003 without starting
the broader named-tool enforcement work reserved for TACD-004.
