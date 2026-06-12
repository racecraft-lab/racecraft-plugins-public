# Research: Reviewer-ready PR packet contract

## Decision: Use one shared rendered packet validator

**Rationale**: Single-PR and split-PR flows share the same reviewer-facing invariants: conventional public title, canonical body sections, UAT compatibility, source/provenance markers, verification evidence, scope evidence, editable prose boundaries, and pre-create blocking. A shared validator keeps failure reporting consistent and avoids split-flow drift.

**Alternatives considered**: Separate validators for single and split flows were rejected because they would duplicate rule logic. Post-create repair was rejected because PRSG-012 requires blocking before reviewers see invalid PRs.

## Decision: Keep JSON Schema as the packet contract and Bash plus `jq` as runtime validation

**Rationale**: JSON Schema 2020-12 documents the packet shape and gives fixture authors a stable target. Runtime validation remains Bash plus `jq` so the plugin does not gain a new schema-validator dependency.

**Alternatives considered**: Adding a dedicated JSON Schema validator was rejected by the no-new-dependencies constraint. Free-form shell variables were rejected because they would weaken fixture coverage and provenance.

## Decision: Treat `generated_title` as structured metadata

**Rationale**: The title needs a final rendered value plus auditable source evidence. The packet stores `type`, `scope`, `description`, `value`, `source_evidence`, and `rejected_candidates` so validation can explain why a fallback was blocked.

**Alternatives considered**: Deriving titles from branch names, spec IDs, slice IDs, task IDs, file paths, or body prose was rejected because those values are internal metadata and not reviewer-ready public descriptions.

## Decision: Source title descriptions from feature titles or slice source boundaries

**Rationale**: Single-PR descriptions should come from the feature/spec display title normalized into an action phrase. Split-PR descriptions should come from PR marker `source_boundary.section`, falling back to layer-plan increment names only in legacy layer-plan mode. Slice IDs remain metadata.

**Alternatives considered**: A generic title such as `feat(speckit-pro): update autopilot` was rejected because it does not name the visible change. Using branch names or PRSG/SPEC identifiers as the description was rejected by the public-readable title requirement; spec identifiers belong only in the conventional title scope.

## Decision: Generate canonical reviewer body sections directly

**Rationale**: `generate-pr-body.sh` should own the canonical sections reviewers need: `Summary`, `What Changed`, `Why It Matters`, `How To Review`, `How To UAT`, `Verification`, `Scope`, and `Known Gaps`. Direct generation gives validation a stable protected block.

**Alternatives considered**: Letting host PR templates provide required sections was rejected because templates may contain stale comments, placeholders, or duplicate headings. Host content can coexist only outside the protected canonical block.

## Decision: Preserve the literal `## UAT Runbook` heading

**Rationale**: Existing SPEC-006a/b compatibility checks expect the literal heading. PRSG-012 adds `How To UAT` for reviewer readability without removing the compatibility heading.

**Alternatives considered**: Replacing `## UAT Runbook` with `How To UAT` was rejected because it would weaken existing compatibility guarantees.

## Decision: Bound safe prose refinement with exact editable markers

**Rationale**: Maintainers can edit narrative language in `Summary`, `What Changed`, and `Why It Matters` while generated governance evidence remains protected. Exact full-line marker pairs make the editable regions deterministic and easy to elide before fingerprinting.

**Alternatives considered**: Allowing arbitrary Markdown edits was rejected because it could damage traceability, UAT, source markers, scope, or verification evidence. Field-specific JSON-only edits were rejected because maintainers naturally refine PR prose in the rendered body.

## Decision: Validate protected-body fingerprints after rendering

**Rationale**: The validator compares a normalized protected-body fingerprint with sanctioned editable blocks elided. This catches changes to source markers, UAT content, traceability, scope, verification evidence, known gaps, and generated governance sections while allowing approved prose edits.

**Alternatives considered**: Checking only the packet JSON shape was rejected because rendered Markdown can still be stale or corrupted. Comparing the whole body byte-for-byte was rejected because it would block allowed prose refinements.

## Decision: Write one validation JSON record per packet

**Rationale**: Deterministic records under `.process/pr-packets/<packet_id>/validation.json` give operators exact remediation evidence and give fixtures a stable assertion target. During PRSG-012 development, failure output is written under `specs/prsg-012-reviewer-ready-pr-packet-contract/.process/`.

**Alternatives considered**: Console-only validation errors were rejected because they are hard to inspect after an autopilot run. A single aggregate-only file was rejected because split-PR mode needs packet-specific evidence.

## Decision: Keep post-create auto-repair out of scope

**Rationale**: PRSG-012 stabilizes packet metadata and blocks invalid packets before `gh pr create`. Repairing already-open PRs can be revisited later if still needed.

**Alternatives considered**: Adding `gh pr edit` repair after creation was rejected because it expands blast radius and does not solve the pre-create reviewer-readiness requirement.

## Decision: Keep one spec and one review slice

**Rationale**: Title generation, body rendering, validation, and PR creation gating all depend on the same packet contract. The projected reviewable LOC is about 350, the advisory estimator is 245, production/reference files are expected to stay at 6-8, and total files should remain under the block threshold by extending existing Layer 7 and Layer 8 post-implementation fixture surfaces instead of creating separate fixture families.

**Alternatives considered**: Splitting title validation from body validation was rejected because both must run before the same PR creation boundary and share packet evidence.
