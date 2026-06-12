# Feature Specification: Reviewer-ready PR packet contract

**Feature Branch**: `prsg-012-reviewer-ready-pr-packet-contract`

**Created**: 2026-06-12

**Status**: Draft

**Input**: User description: "Make autopilot-generated PR titles and descriptions deterministic, reviewer-ready, and validated before `gh pr create` for single-PR and split-PR flows."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Specific conventional PR titles (Priority: P1)

As a reviewer, I see a specific conventional PR title that names the visible or operator-visible change before I open the PR body.

**Why this priority**: The PR title is the first review and squash-merge signal. If it is vague, stale, or non-conventional, the final commit history and review queue are degraded before body details can help.

**Independent Test**: Generate packets for a single-PR run and a split-PR run, then inspect only the rendered titles and validation result to confirm each title is specific, conventional, and packet-owned.

**Acceptance Scenarios**:

1. **Given** autopilot prepares a single PR for a visible or operator-visible change, **When** the PR packet is rendered, **Then** the title follows conventional commit form and names the concrete change.
2. **Given** autopilot prepares split PRs for multiple slices, **When** each packet title is rendered, **Then** each title names the slice-specific change rather than a generic batch label.
3. **Given** a rendered title contains stale placeholder text, banned wording, or a generic non-specific label, **When** packet validation runs, **Then** validation blocks and reports exact title evidence to fix.

---

### User Story 2 - Structured reviewer body (Priority: P1)

As a reviewer, I see a neutral structured PR body with Summary, What Changed, Why It Matters, How To Review, How To UAT, Verification, Scope, and Known Gaps.

**Why this priority**: Reviewers need a stable reading order and complete review evidence without depending on manual cleanup after PR creation.

**Independent Test**: Render a valid packet body and confirm the required headings, source markers, UAT compatibility heading, verification evidence, scope evidence, and known-gap language are present in the final text.

**Acceptance Scenarios**:

1. **Given** a valid rendered packet body, **When** a reviewer opens it, **Then** it contains the required reviewer-facing sections in a stable order.
2. **Given** the same packet body, **When** compatibility content is checked, **Then** the literal `## UAT Runbook` heading remains present alongside the reviewer-facing How To UAT section.
3. **Given** a body omits verification evidence, scope evidence, or required source markers, **When** validation runs, **Then** validation blocks before PR creation and names the missing evidence.
4. **Given** a body uses banned labels such as `ELI5` or `Plain-English Summary`, **When** validation runs, **Then** validation rejects the packet even if other sections are present.

---

### User Story 3 - Pre-create validation block (Priority: P1)

As an operator, invalid packets block before PR creation with exact remediation evidence.

**Why this priority**: The failure must happen before `gh pr create` so operators do not need broad post-create repair and reviewers do not receive stale or incomplete PRs.

**Independent Test**: Run packet validation against valid and invalid packet fixtures for every PR creation mode and confirm invalid packets do not reach PR creation.

**Acceptance Scenarios**:

1. **Given** a packet is missing a required heading, **When** validation runs, **Then** it writes a failed validation result and blocks before PR creation.
2. **Given** a packet passes validation, **When** PR creation proceeds, **Then** the PR creation path uses the generated title and generated body file.
3. **Given** split-PR mode renders multiple packets and one packet is invalid, **When** validation runs, **Then** the invalid packet is blocked with packet-specific evidence before its PR is created.

---

### User Story 4 - Safe prose refinement (Priority: P2)

As a maintainer, I can refine sanctioned prose fields without damaging generated governance sections, source markers, UAT content, traceability, scope, or verification evidence.

**Why this priority**: Maintainers need room to improve reviewer-facing language while preserving deterministic governance and reviewability guarantees.

**Independent Test**: Modify only sanctioned prose fields in a rendered packet and confirm validation still passes, then modify protected governance evidence and confirm validation rejects the change.

**Acceptance Scenarios**:

1. **Given** a maintainer edits sanctioned narrative fields, **When** the rendered packet still preserves protected evidence, **Then** validation accepts the packet.
2. **Given** an edit removes or corrupts source markers, UAT content, traceability, scope, or verification evidence, **When** validation runs, **Then** validation rejects the packet and identifies the damaged invariant.
3. **Given** a host PR template safely contributes additional content, **When** the final packet renders, **Then** the required packet-owned sections and validation guarantees remain intact.

---

### Edge Cases

- A single-PR packet and a split-PR packet require different titles, UAT details, and verification evidence for the same feature.
- A host PR template includes legacy headings, template comments, placeholder variables, or example text in the final rendered body.
- Manual UAT is not applicable for a packet, but the reviewer still needs explicit How To UAT and `## UAT Runbook` content explaining that no manual UAT path is required.
- Known Gaps has no open gaps; the body must still say so explicitly rather than omit the section.
- A source marker appears only inside a code fence, HTML comment, generated fixture, or non-rendered area.
- One split packet fails validation while other split packets pass.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST generate a packet-owned PR title for the single-PR path.
- **FR-002**: The system MUST generate a packet-owned PR title for each split-PR path.
- **FR-003**: Every generated PR title MUST follow conventional commit form and name the visible or operator-visible change.
- **FR-004**: Every PR creation path MUST use the generated title and generated body file as the PR title and body inputs.
- **FR-005**: A shared deterministic PR packet validator MUST run before every PR creation attempt.
- **FR-006**: The validator MUST evaluate rendered title and body text after packet rendering, not only schema or source data shape.
- **FR-007**: The validator MUST reject stale placeholders, unfilled template comments, unexpanded variables, and example text that remains in the rendered packet.
- **FR-008**: The validator MUST reject rendered bodies missing any required reviewer-facing heading: Summary, What Changed, Why It Matters, How To Review, How To UAT, Verification, Scope, or Known Gaps.
- **FR-009**: Rendered bodies MUST keep the literal `## UAT Runbook` compatibility heading while also providing the reviewer-facing How To UAT section.
- **FR-010**: The validator MUST reject rendered packets missing required source markers for generated packet content and evidence sources.
- **FR-011**: The validator MUST reject rendered packets missing verification evidence or scope evidence.
- **FR-012**: The validator MUST reject banned labels including `ELI5` and `Plain-English Summary`.
- **FR-013**: Validation failures MUST block before PR creation and report remediation evidence that names the failed rule, packet target, affected section, and relevant text excerpt when available.
- **FR-014**: Validation results MUST be written as JSON under the feature `.process` tree with status, rule outcomes, packet identity, title/body paths, and failure details.
- **FR-015**: Blocking validation failures MUST append a concise workflow event that records the blocked packet and remediation evidence location.
- **FR-016**: The packet contract MUST allow sanctioned prose refinements while protecting generated governance sections, source markers, UAT content, traceability, scope, and verification evidence.
- **FR-017**: Host PR template support MAY coexist only when the final rendered packet still satisfies the packet contract.
- **FR-018**: PRSG-012 MUST treat post-create auto-repair of already-open PRs as out of scope.

### Constraints

- No new runtime dependencies beyond the repository's existing shell and JSON-processing tooling.
- Deterministic packet generation and validation logic belongs in reusable scripts with fixture-backed validation.
- Existing UAT runbook guarantees from SPEC-006a/b must not be weakened.
- Codex-facing mirrored autopilot behavior must preserve parity with the primary autopilot contract.

### Reviewability Notes *(if applicable)*

- Typed reviewability exceptions are not expected for PRSG-012.
- Generated packet fixtures, generated zones, `.process` files, PR bodies, and code fences must not be treated as valid provenance for protected source markers.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: contracts, docs/process
- **Projected reviewable LOC**: 500-900 excluding generated fixtures and validation result output
- **Projected production files**: 5-8
- **Projected total files**: 12-18
- **Budget result**: within budget
- **Split decision**: Keep as one spec because title generation, body rendering, validation, and PR creation gating share one reviewer packet contract. Fixture and documentation updates can be reviewed in the same vertical slice without splitting the behavior.

### PR Review Packet Requirements *(mandatory)*

- PR descriptions MUST include what changed, why it matters, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.
- Validation evidence for PRSG-012 MUST show both passing packets and blocked packets across single-PR and split-PR flows.

### Key Entities *(include if feature involves data)*

- **PR Packet**: A rendered PR title and body for one PR target, including mode, slice identity when applicable, required headings, UAT content, source markers, scope evidence, verification evidence, and known-gap language.
- **Packet Validation Result**: A JSON record describing pass or fail status, evaluated rules, packet identity, title/body locations, and remediation evidence for failures.
- **Workflow Event**: A concise process log entry written when validation blocks a packet before PR creation.
- **Sanctioned Prose Field**: A maintainer-editable narrative field that may be refined without changing protected governance or evidence sections.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of supported PR creation attempts validate a rendered packet before PR creation is attempted.
- **SC-002**: 100% of seeded invalid packet examples for missing headings, stale placeholders, banned labels, missing source markers, missing verification evidence, and missing scope evidence are blocked with at least one exact remediation evidence item.
- **SC-003**: 100% of seeded valid packet examples render a conventional PR title, all required reviewer-facing sections, and the literal `## UAT Runbook` compatibility heading.
- **SC-004**: A reviewer can identify what changed, why it matters, review order, UAT path, verification evidence, scope, and known gaps from a generated PR body in under 2 minutes.
- **SC-005**: 100% of sanctioned prose refinement examples retain protected governance evidence and pass validation.
- **SC-006**: No valid generated packet requires manual cleanup after rendering before PR creation.

## Assumptions

- Existing SPEC-006a/b UAT runbook wiring remains the source of UAT content for generated packets.
- A required source marker is an explicit rendered marker outside comments, code fences, generated fixtures, and other non-provenance text.
- Sanctioned prose fields are limited to declared reviewer-facing narrative fields; generated governance and evidence fields remain validator-protected.
- Validation JSON for this feature is written under `specs/prsg-012-reviewer-ready-pr-packet-contract/.process`.
- PRSG-012 covers generation and validation before PR creation only; repair of already-open PRs is deferred to a later feature if needed.
