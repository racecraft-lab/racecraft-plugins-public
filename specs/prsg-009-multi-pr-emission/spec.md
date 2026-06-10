# Feature Specification: PRSG-009 multi-PR emission

**Feature Branch**: `prsg-009-multi-pr-emission`

**Created**: 2026-06-10

**Status**: Draft

**Input**: User description: "The current post-implementation flow flattens implementation output into one PR even when PRSG-008 has produced multiple reviewable slices. PRSG-009 must consume the PRSG-008 layer plan, emit ordered Style B incremental stack PRs after full implementation and verification, keep the spec MOC PR table durable, define scoped CI and restack behavior, stop before opening failed slice PRs, and preserve Codex parity for mirrored skill/reference changes."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Emit ordered slice PRs from the layer plan (Priority: P1)

As a maintainer reviewing SpecKit-generated implementation work, I want the autopilot to create one ordered PR per PRSG-008 reviewable layer so each review unit stays small, dependency-aware, and aligned with the declared slice plan.

**Why this priority**: This is the primary governance fix. Without deterministic multi-PR emission, PRSG-008 can split work correctly but reviewers still receive one oversized PR.

**Independent Test**: Use a completed implementation with a PRSG-008 layer plan containing multiple layers, run the emission phase, and verify that the emitted branch and PR sequence exactly follows the layer order without adding new slicing heuristics.

**Acceptance Scenarios**:

1. **Given** a verified implementation and a `plan-layers.sh` output with three ordered layers, **When** the emission phase runs, **Then** it creates three ordered PRs whose branch bases and review order match the layer plan.
2. **Given** a layer plan containing a single layer, **When** the emission phase runs, **Then** it emits one PR using the same emission contract without falling back to the previous all-changes PR path.
3. **Given** a layer plan that includes file ownership for each slice, **When** slice branches are created, **Then** each branch contains only the declared file operations for that slice plus explicitly required shared bookkeeping.

---

### User Story 2 - Persist PR table and resume evidence after each slice (Priority: P2)

As an autopilot operator, I want the spec MOC PR table, workflow status, and `autopilot-state.json` updated after each successful slice PR so review navigation, resume behavior, and recovery evidence survive interruptions.

**Why this priority**: Multi-PR emission is only operable if partial progress is durable. Operators need to resume without duplicating PRs, losing ordering, or reopening already-failed slices.

**Independent Test**: Interrupt emission after a successful slice PR, resume the workflow, and verify that already-opened PRs are recognized from durable state while pending slices continue from the next unstarted layer.

**Acceptance Scenarios**:

1. **Given** slice PR 1 opens successfully, **When** the workflow records progress, **Then** the spec MOC PR table includes PR 1 with branch, base, scope, verification, status, and review order fields before slice PR 2 begins.
2. **Given** emission is interrupted after slice PR 2, **When** the operator resumes, **Then** the workflow reads durable MOC and state entries, skips already-opened slice PRs, and continues with the next pending slice.
3. **Given** a scoped verification command fails for a slice, **When** the emission phase handles the failure, **Then** no PR is opened for that slice and the workflow plus `autopilot-state.json` record the failed command, evidence location, and blocked slice identity.

---

### User Story 3 - Define stack topology, scoped CI, and restack behavior (Priority: P3)

As a maintainer, I want branch topology, scoped CI mapping, and restack behavior defined so stacked review remains usable through squash-merge review loops.

**Why this priority**: Reviewers need predictable branch bases and verification expectations after emission works. This makes the stack maintainable without expanding PRSG-009 into new routing logic.

**Independent Test**: Simulate a Style B incremental stack with at least two slice PRs, squash-merge the lower slice, and verify that the remaining branches can be restacked according to documented rules while preserving review scope.

**Acceptance Scenarios**:

1. **Given** a Style B incremental stack, **When** the first slice PR is opened, **Then** it targets the integration base branch and each later slice branch targets the immediately preceding slice branch.
2. **Given** the lower slice is squash-merged, **When** the stack is restacked, **Then** remaining open slice branches are rebased or retargeted in order without changing their declared file-operation scope.
3. **Given** a slice declares structural and script verification gates, **When** its PR packet is prepared, **Then** the PR includes the scoped command mapping and the successful evidence required for that slice.

### Edge Cases

- The layer plan is missing, unreadable, empty, or not parseable.
- The layer plan references files not changed by the completed implementation.
- A slice contains only shared bookkeeping files needed for durable emission state.
- A slice branch already exists locally or remotely from a previous interrupted run.
- A slice PR already exists, was closed, or was merged before resume.
- A lower stack PR is squash-merged while higher slice PRs remain open.
- Scoped verification passes for an earlier slice but fails for a later slice.
- GitHub PR creation succeeds but state persistence fails immediately afterward.
- `.process/prs.json` is stale, missing, or schema v1 while `autopilot-state.json` records created slice PRs.
- Codex and Claude mirrored skill/reference files differ for the same emission behavior.


## Clarifications

### Session 1 - State and Resume Contract (2026-06-10)

- Multi-PR emission state MUST live in a top-level `multi_pr_emission` object in `docs/ai/specs/.process/autopilot-state.json`, separate from the existing workflow `plan[]` and `layer_plan` entries.
- `multi_pr_emission` MUST include `schema_version`, `status`, `source_layer_plan`, `base_branch`, `base_sha`, `next_slice_id`, `reconciled_at`, `slices[]`, and optional `failed_slice`.
- Each slice state entry MUST include `slice_id`, review order, expected branch, expected base branch, head SHA, declared files, declared scoped tests, scoped verification record, PR record, status, and last error.
- Created slice PR records MUST also be written to `specs/<branch>/.process/prs.json` using `schemaVersion: 2`; the spec MOC PRS zone is generated from this manifest, not from `autopilot-state.json` or workflow prose.
- PRS manifest schema v2 MUST stay bounded to reviewer-navigation fields: review order, layer or slice identity, branch, base branch, PR number or URL, declared file scope, scoped verification evidence pointer, status, and SHA fields as available. It MUST keep schema v1 rendering backward-compatible.
- `autopilot-state.json` remains the machine-readable resume surface for pending next slice, failed scoped-test evidence, reconciliation facts, retry policy, and other orchestration state. Full command logs and bulky PR body content MUST be stored by path, not inline in MOC rows.
- Persistence order MUST be: persist branch/base/head metadata after branch creation; persist scoped verification command and evidence after verification passes; after `gh pr create`, query the PR by expected head/base and persist number, URL, state, refs, and SHAs; then update `.process/prs.json`, regenerate the MOC, update workflow evidence, and only then advance `next_slice_id`.
- Resume MUST reconcile expected local/remote branches and GitHub PRs by expected head branch and base across all PR states before creating anything new. Existing expected-head PRs MUST be mapped to `pending`, `branch_created`, `pr_opened`, `merged`, `closed`, or `failed`; the emitter MUST NOT create duplicate PRs for an expected head branch.
- Failed scoped verification MUST record `slice_id`, `failed_at`, phase `scoped_verification`, command, exit status, evidence path, stdout/stderr tail, head SHA, declared tests, and retry policy in both `multi_pr_emission.failed_slice` and the slice `last_error`. Full logs live under `specs/prsg-009-multi-pr-emission/.process/emission/<slice_id>/`.


### Session 2 - Branch and PR Contract (2026-06-10)

- Emitted slice branches MUST use `<feature-branch>/<NN>-<slice-id>` where `<NN>` is zero-padded by total slice count and `<slice-id>` is a slug derived from the PRSG-008 increment identifier. Each candidate branch name MUST pass `git check-ref-format --branch` before use.
- The first slice PR MUST use explicit `--base <integration-base> --head <slice-01-branch>`. Each later slice PR MUST use explicit `--base <previous-slice-branch> --head <current-slice-branch>`. The emitter MUST NOT rely on `gh pr create` base/head defaults.
- Each slice branch MUST be pushed before `gh pr create`, and PR creation MUST use `--body-file` generated from the review packet path for that slice.
- `generate-pr-body.sh` MUST preserve its current positional usage and MAY accept an optional `--slice-packet <json-file>` argument. The packet supplies `slice_id`, review order, base branch, head branch, declared files/tests, verification evidence, restack note, and PRS row fields.
- For schemaVersion 2 PRS rows, open slice PRs display `head_sha` as the row SHA. After merge, the renderer MUST prefer `merged_sha` when available. Open PR head commits MUST NOT be written into `merged_sha`.
- After `gh pr create`, the emitter MUST query GitHub by expected head ref and base ref across all PR states. It MUST persist PR number, URL, state, base/head refs, head SHA, and merge SHA if available before regenerating the MOC or advancing `next_slice_id`. Zero or multiple matching PRs is a reconciliation failure that stops before duplicate creation.


### Session 3 - CI and Restack Contract (2026-06-10)

- Scoped CI for PRSG-009 means per-slice scoped verification commands are selected from the project command table, run during emission, and recorded in the slice packet, PR body, `.process/prs.json` evidence pointer, workflow evidence, and `autopilot-state.json`. PRSG-009 MUST NOT modify `.github/workflows/pr-checks.yml`; existing PR Checks continue unchanged.
- Each slice packet MUST include `scoped_verification.commands[]` entries with command, gate type, reason, required flag, evidence path, exit status, and started/finished timestamps. The entries are seeded from PRSG-008 files/tests plus project commands such as `STRUCTURAL`, `SCRIPT_UNIT`, and `DEFAULT_VERIFY` as the full-suite reference.
- `gh-stack` MAY be used only when `gh stack` is installed and non-mutating stack inspection succeeds for an existing active stack. PRSG-009 MUST keep explicit `gh pr create --base --head --body-file` as the required emission path.
- The fallback `restack.sh` helper MUST default to dry-run and require `--apply` for mutation. It MUST accept `--state`, `--manifest`, `--base`, `--remote`, and `--start-after`; emit JSON stdout; write deterministic diagnostics to stderr; and use distinct exit codes for success, conflicts, input errors, dirty worktree, and `git`/`gh` failures.
- Full regression verification MUST run once before emission and store evidence by path for slice packets to reference. A fresh `DEFAULT_VERIFY` is required after restack before final/base merge evidence is considered current. The full suite MUST NOT be required on every slice PR.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST consume PRSG-008 `plan-layers.sh` output as the authoritative ordering source for multi-PR emission.
- **FR-002**: The system MUST NOT introduce new atomicity, routing, or slicing heuristics in PRSG-009; layer membership must come from the existing PRSG-008 plan.
- **FR-003**: The system MUST emit slice PRs only after full implementation and required verification have completed for the overall feature.
- **FR-004**: The system MUST use Style B incremental stack branches, where the first slice targets the integration base and each later slice targets the previous slice branch.
- **FR-004a**: Slice PR creation MUST pass explicit `--base`, `--head`, and `--body-file` arguments to `gh pr create`; default base/head inference is not allowed.
- **FR-005**: The system MUST create one slice branch and one PR per planned layer when scoped verification for that slice succeeds.
- **FR-006**: The system MUST ensure each slice branch contains only that slice's declared file operations plus explicitly required shared workflow or state updates.
- **FR-007**: The system MUST define deterministic branch naming for emitted slice branches so resume can identify them without ambiguity.
- **FR-007a**: Slice branches MUST use `<feature-branch>/<NN>-<slice-id>` with zero-padded order and a validated PRSG-008 increment slug.
- **FR-008**: The system MUST update the spec MOC PR table after each successful PR creation before attempting the next slice.
- **FR-008a**: Created slice PR records MUST be written to `specs/<branch>/.process/prs.json` using schemaVersion 2, while preserving backward-compatible rendering for schemaVersion 1 manifests.
- **FR-008b**: SchemaVersion 2 PRS rendering MUST display `head_sha` for open PRs and prefer `merged_sha` once available; open PR head commits MUST NOT be written into `merged_sha`.
- **FR-009**: The spec MOC PR table MUST record, for each slice PR, the review order, branch, base branch, PR URL or number, layer identity, declared file scope, scoped verification evidence, and current status.
- **FR-010**: The system MUST persist resume state in `autopilot-state.json` after each successful PR creation, including completed slice identity and pending next slice identity.
- **FR-010a**: The resume state MUST include a top-level `multi_pr_emission` object with schema version, overall emission status, source layer-plan identity, base branch and SHA, next slice identity, reconciliation timestamp, slice records, and optional failed-slice record.
- **FR-011**: The system MUST detect already-created slice branches or PRs during resume and reconcile them with the spec MOC PR table before creating additional PRs.
- **FR-011a**: Resume reconciliation MUST query expected local and remote branches plus GitHub PRs by expected head and base across all PR states before creating any new branch or PR.
- **FR-012**: The system MUST stop before opening a slice PR when that slice's scoped verification fails.
- **FR-013**: On scoped verification failure, the system MUST record the failed slice identity, failed command, exit status, and evidence location in the workflow record and `autopilot-state.json`.
- **FR-013a**: Failed scoped verification state MUST include the failed time, phase, command, exit status, evidence path, stdout/stderr tail, head SHA, declared tests, and retry policy; full logs MUST live under the spec `.process/emission/<slice_id>/` directory.
- **FR-014**: The system MUST NOT open known-bad draft PRs for slices with failed scoped verification.
- **FR-015**: The system MUST map each slice to the scoped verification gates required by the project command table, including structural and script-unit checks where applicable.
- **FR-015b**: PRSG-009 scoped CI means recorded scoped verification evidence in slice packets and PR bodies; it MUST NOT modify `.github/workflows/pr-checks.yml`.
- **FR-015a**: Per-slice PR body generation MUST support a bounded slice packet containing slice identity, review order, branch/base refs, declared files/tests, verification evidence, restack note, and PRS row fields while keeping existing single-PR invocation compatible.
- **FR-016**: The system MUST include scoped CI or verification mapping in each slice PR packet so reviewers can see which commands protect that review unit.
- **FR-016a**: Slice packets MUST include `scoped_verification.commands[]` records with command, gate type, reason, required flag, evidence path, exit status, and started/finished timestamps.
- **FR-017**: The system MUST define restack behavior for squash-merge review loops, including how remaining branches are rebased or retargeted after a lower slice merges.
- **FR-017a**: `gh-stack` MUST be optional and used only for safely detected restack/sync operations on existing active stacks; PRSG-009 MUST NOT use it as the required PR creation mechanism.
- **FR-017b**: The fallback `restack.sh` helper MUST be dry-run by default, require `--apply` for mutations, accept `--state`, `--manifest`, `--base`, `--remote`, and `--start-after`, emit JSON stdout, and use distinct exit codes for success, conflicts, input errors, dirty worktree, and `git`/`gh` failures.
- **FR-018**: Restack behavior MUST preserve the declared file-operation scope of each unmerged slice.
- **FR-019**: The system MUST record enough recovery evidence to distinguish pending, opened, failed, closed, and merged slice states.
- **FR-020**: The system MUST preserve Codex parity for mirrored skill and reference changes that implement or document multi-PR emission behavior.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: harness/adapter, seed/config
- **Projected reviewable LOC**: 350-650 excluding generated distribution mirrors
- **Projected production files**: 3-6
- **Projected total files**: 8-14 including mirrored Codex/Claude references and focused tests
- **Budget result**: warning accepted
- **Split decision**: This remains one spec because the scope is constrained to emission, resume, scoped verification mapping, and restack behavior that depend on one contract. New review-routing heuristics and deeper atomicity backstops are explicitly deferred to PRSG-010.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Layer Plan**: Ordered PRSG-008 output that identifies reviewable layers, declared file operations, and verification expectations used by PRSG-009 as input.
- **Slice Branch**: A deterministic branch for one layer in the Style B incremental stack, named `<feature-branch>/<NN>-<slice-id>`, with a known base, review order, and file-operation scope.
- **Slice PR**: The GitHub pull request opened from a slice branch using explicit head/base refs and a generated `--body-file`, containing PR packet metadata, scoped verification evidence, full-suite evidence reference, and review navigation.
- **Spec MOC PR Table**: Durable per-spec navigation table generated from `specs/<branch>/.process/prs.json`. Schema v2 records emitted PRs, statuses, branch topology, scope, evidence pointers, order, and available SHA fields after each successful slice; schema v1 remains supported for older manifests.
- **Autopilot State Entry**: Machine-readable resume and recovery state under the top-level `multi_pr_emission` object. It records slice progress, pending work, failed evidence, branch/PR reconciliation facts, and retry policy.
- **Restack Operation**: The ordered recovery action that updates remaining slice branches after a lower stack PR is squash-merged, using safely detected `gh-stack` restack/sync when available or a deterministic dry-run-first `restack.sh` fallback.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Given a valid three-layer PRSG-008 plan, emission creates three PRs in the same order with branch bases matching Style B incremental stack rules.
- **SC-002**: After each successful slice PR, `.process/prs.json` schema v2, the generated spec MOC PR table, and `autopilot-state.json` contain enough data to resume without duplicating that PR.
- **SC-003**: If a later slice fails scoped verification, zero PRs are opened for that failed slice and the failed command evidence is recorded in both durable workflow state surfaces.
- **SC-004**: Each emitted slice PR includes review order, scope budget, declared file-operation scope, scoped verification evidence, traceability, non-goals, known gaps, rollback or restack notes, and a reference to full-suite evidence captured before emission.
- **SC-005**: After a lower slice is squash-merged, remaining slice branches can be restacked or retargeted in documented order while preserving their declared review scope.
- **SC-006**: Structural validation and script-unit tests cover the multi-PR emission contract, resume reconciliation, failed-slice stop behavior, optional `gh-stack` detection, fallback restack behavior, and Codex parity checks.

## Assumptions

- PRSG-008 already produces a deterministic layer plan with enough file-operation data for emission.
- The implementation phase has already completed before PRSG-009 emission begins.
- The existing project verification commands are limited to structural and script-unit shell checks for this repository.
- GitHub remains the PR host for emitted slice PRs.
- `autopilot-state.json` is the durable machine-readable resume surface, while the spec MOC PR table is the durable reviewer-facing navigation surface.
- Generated or mirrored distribution files may be included when needed for parity, but they do not change the behavioral scope of PRSG-009.
